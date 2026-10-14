// Upstream request recorder.
//
// A passthrough HTTP proxy that sits between the nconnect daemon and the two
// services it calls during a benchmark task:
//
//   http://127.0.0.1:<port>/v1/...          -> https://api.tokenfactory.nebius.com/v1/...
//   http://127.0.0.1:<port>/typesafe/v1/... -> https://api.typesafe.ai/v1/...
//
// nconnect is pointed at it through settings it already supports
// (NEBIUS_BASE_URL and NCONNECT_AUTO_DECIDER_URL). For every request it appends
// one JSON line: when it started, how long headers and the first byte took,
// which model was asked for and answered, the token usage the provider
// reported, and what kind of call it was. It never records headers (API keys
// live there), prompts, code or completions. Bodies are inspected in memory
// only to classify the call and read the usage block.
//
// Usage: node recorder.mjs --out <file.jsonl>   (prints {"port": N} when ready)

import { createHash } from "node:crypto";
import { appendFileSync } from "node:fs";
import http from "node:http";

const args = process.argv.slice(2);
const outFile = args[args.indexOf("--out") + 1];
if (!outFile || args.indexOf("--out") === -1) {
  console.error("usage: node recorder.mjs --out <file.jsonl>");
  process.exit(2);
}

const UPSTREAMS = [
  { prefix: "/typesafe/", origin: "https://api.typesafe.ai", strip: "/typesafe" },
  { prefix: "/", origin: "https://api.tokenfactory.nebius.com", strip: "" },
];
const HOP_HEADERS = new Set([
  "host", "connection", "keep-alive", "proxy-connection", "transfer-encoding", "upgrade",
  "content-length", "accept-encoding", "te", "trailer",
]);
const RESPONSE_DROP = new Set(["content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive"]);
// The markers nconnect itself uses to recognise Claude Code's background calls.
const TITLE_MARKERS = ["You are naming a coding session", "Generate a concise, sentence-case title"];
const CLASSIFIER_MARKER = "monitor for autonomous AI coding agents";
const WARMUP_MARKER = "warm-up: reply with exactly OK";

let sequence = 0;

function textOf(content) {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map((part) => (typeof part?.text === "string" ? part.text : "")).join("\n");
  }
  return "";
}

function describeNebius(body) {
  const messages = Array.isArray(body.messages) ? body.messages : [];
  const tools = Array.isArray(body.tools) ? body.tools.length : 0;
  const system = messages.filter((m) => m?.role === "system").map((m) => textOf(m.content)).join("\n");
  let kind = tools > 0 ? "agent" : "toolless";
  if (tools === 0 && TITLE_MARKERS.some((marker) => system.includes(marker))) kind = "background_title";
  else if (tools === 0 && system.includes(CLASSIFIER_MARKER)) kind = "background_classifier";
  return {
    kind,
    model: body.model ?? null,
    stream: body.stream === true,
    message_count: messages.length,
    tool_count: tools,
    max_tokens: body.max_tokens ?? body.max_completion_tokens ?? null,
    reasoning_effort: body.reasoning_effort ?? null,
    has_stream_usage: body.stream_options?.include_usage === true,
  };
}

function describeTypesafe(body) {
  const state = typeof body.state === "string" ? body.state : JSON.stringify(body.state ?? "");
  return {
    kind: state.includes(WARMUP_MARKER) ? "jev_warmup" : "jev",
    model: body.model ?? null,
    questions: Object.keys(body.questions ?? {}),
    state_chars: state.length,
  };
}

function usageOf(usage) {
  if (!usage || typeof usage !== "object") return null;
  return {
    prompt_tokens: usage.prompt_tokens ?? usage.input_tokens ?? null,
    completion_tokens: usage.completion_tokens ?? usage.output_tokens ?? null,
    total_tokens: usage.total_tokens ?? null,
    // Nebius reports cache hits DeepSeek-style; OpenAI-style is kept as a fallback.
    cached_tokens: usage.prompt_cache_hit_tokens ?? usage.prompt_tokens_details?.cached_tokens ?? usage.cached_tokens ?? null,
    cache_miss_tokens: usage.prompt_cache_miss_tokens ?? null,
    // A subset of completion_tokens, never added to it.
    reasoning_tokens: usage.completion_tokens_details?.reasoning_tokens ?? usage.reasoning_tokens ?? null,
    raw_keys: Object.keys(usage),
  };
}

function write(record) {
  appendFileSync(outFile, `${JSON.stringify(record)}\n`);
}

const server = http.createServer(async (req, res) => {
  const id = ++sequence;
  const started = performance.now();
  const record = { id, t_start: new Date().toISOString(), method: req.method, path: req.url.split("?")[0] };
  const upstream = UPSTREAMS.find((u) => req.url.startsWith(u.prefix));
  const target = upstream.origin + req.url.slice(upstream.strip.length);
  record.upstream = upstream.origin.replace("https://", "");

  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const body = Buffer.concat(chunks);
  record.request_bytes = body.length;
  record.request_sha256 = createHash("sha256").update(body).digest("hex").slice(0, 16);
  try {
    const parsed = body.length ? JSON.parse(body.toString("utf8")) : {};
    Object.assign(record, upstream.strip ? describeTypesafe(parsed) : describeNebius(parsed));
  } catch {
    record.kind = "unparsed";
  }

  const headers = {};
  for (const [name, value] of Object.entries(req.headers)) {
    if (!HOP_HEADERS.has(name.toLowerCase())) headers[name] = value;
  }
  headers["accept-encoding"] = "identity";

  const controller = new AbortController();
  let clientGone = false;
  res.on("close", () => {
    if (!res.writableEnded) {
      clientGone = true;
      controller.abort();
    }
  });

  let response;
  try {
    response = await fetch(target, {
      method: req.method,
      headers,
      body: ["GET", "HEAD"].includes(req.method) ? undefined : body,
      signal: controller.signal,
    });
  } catch (err) {
    record.ms_total = Math.round(performance.now() - started);
    record.error = clientGone ? "client_aborted" : String(err?.cause?.code ?? err?.name ?? err);
    write(record);
    if (!res.headersSent && !clientGone) {
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: { message: "recorder could not reach upstream", type: "upstream_error" } }));
    }
    return;
  }
  record.status = response.status;
  record.ms_headers = Math.round(performance.now() - started);
  const outHeaders = {};
  response.headers.forEach((value, name) => {
    if (!RESPONSE_DROP.has(name)) outHeaders[name] = value;
  });
  res.writeHead(response.status, outHeaders);

  const contentType = response.headers.get("content-type") ?? "";
  const isSse = contentType.includes("text/event-stream");
  const decoder = new TextDecoder();
  let pending = "";
  let whole = "";
  let bytes = 0;
  let events = 0;
  const scanLine = (line) => {
    if (!line.startsWith("data:")) return;
    const data = line.slice(5).trim();
    if (!data || data === "[DONE]") return;
    events += 1;
    if (!data.includes('"usage"') && !data.includes('"finish_reason"') && record.response_model) return;
    try {
      const event = JSON.parse(data);
      if (event.model && !record.response_model) record.response_model = event.model;
      const finish = event.choices?.[0]?.finish_reason;
      if (finish) record.finish_reason = finish;
      if (event.usage) record.usage = usageOf(event.usage);
      if (event.error) record.stream_error = event.error.type ?? event.error.code ?? "error";
    } catch {
      // A partial or non-JSON data line: nothing to record.
    }
  };
  try {
    for await (const chunk of response.body) {
      if (bytes === 0) record.ms_first_byte = Math.round(performance.now() - started);
      bytes += chunk.length;
      res.write(chunk);
      const text = decoder.decode(chunk, { stream: true });
      if (isSse) {
        pending += text;
        const lines = pending.split("\n");
        pending = lines.pop() ?? "";
        lines.forEach(scanLine);
      } else if (whole.length < 8_000_000) {
        whole += text;
      }
    }
    if (isSse && pending) scanLine(pending);
    res.end();
  } catch (err) {
    record.error = clientGone ? "client_aborted" : String(err?.cause?.code ?? err?.name ?? err);
    res.destroy();
  }
  if (!isSse && whole) {
    try {
      const json = JSON.parse(whole);
      if (json.model) record.response_model = json.model;
      if (json.usage) record.usage = usageOf(json.usage);
      const finish = json.choices?.[0]?.finish_reason;
      if (finish) record.finish_reason = finish;
      if (json.error) record.error_type = json.error.type ?? json.error.code ?? "error";
      const tier = json.answers?.tier;
      if (tier) {
        // Jev's decision itself: the choice and its probabilities.
        record.jev_choice = tier.choice ?? null;
        record.jev_probabilities = tier.probabilities ?? null;
      }
    } catch {
      record.response_unparsed = true;
    }
  }
  record.response_bytes = bytes;
  record.sse_events = isSse ? events : undefined;
  record.ms_total = Math.round(performance.now() - started);
  write(record);
});

server.keepAliveTimeout = 120_000;
server.requestTimeout = 0;
server.headersTimeout = 0;
server.listen(0, "127.0.0.1", () => {
  process.stdout.write(`${JSON.stringify({ port: server.address().port })}\n`);
});
for (const signal of ["SIGTERM", "SIGINT"]) {
  process.on(signal, () => server.close(() => process.exit(0)));
  process.on(signal, () => setTimeout(() => process.exit(0), 2000).unref());
}
