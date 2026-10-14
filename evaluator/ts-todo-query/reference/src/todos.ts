export type Status = "open" | "done";

export interface Todo {
  id: number;
  title: string;
  status: Status;
  tags: string[];
  /** Due date as "YYYY-MM-DD", or null when there is none. */
  due: string | null;
  /** Milliseconds since the epoch, from the injected clock. */
  createdAt: number;
}

export interface NewTodo {
  title: string;
  tags?: string[];
  due?: string | null;
}

export interface TodoQuery {
  status?: "open" | "done" | "all";
  tags?: string[];
  text?: string;
  dueBefore?: string;
  sort?: "id" | "created" | "due" | "title";
  order?: "asc" | "desc";
}

const STATUSES = ["open", "done", "all"];
const SORTS = ["id", "created", "due", "title"];
const ORDERS = ["asc", "desc"];

export function isCalendarDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const [year, month, day] = [Number(match[1]), Number(match[2]), Number(match[3])];
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

function compare(a: string | number, b: string | number): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

export class TodoService {
  private todos: Todo[] = [];
  private nextId = 1;
  private clock: () => number;

  constructor(clock: () => number = Date.now) {
    this.clock = clock;
  }

  add(input: NewTodo): Todo {
    const title = input.title.trim();
    if (title === "") throw new TypeError("title must not be empty");
    const todo: Todo = {
      id: this.nextId++,
      title,
      status: "open",
      tags: [...(input.tags ?? [])],
      due: input.due ?? null,
      createdAt: this.clock(),
    };
    this.todos.push(todo);
    return todo;
  }

  complete(id: number): Todo {
    const todo = this.todos.find((t) => t.id === id);
    if (!todo) throw new Error(`no todo with id ${id}`);
    todo.status = "done";
    return todo;
  }

  /** All todos in id order. */
  list(): Todo[] {
    return [...this.todos];
  }

  /** Filter and sort todos; see docs/query.md. */
  query(query: TodoQuery = {}): Todo[] {
    const status = query.status ?? "all";
    const sort = query.sort ?? "id";
    const order = query.order ?? "asc";
    if (!STATUSES.includes(status)) throw new RangeError(`invalid status: ${status}`);
    if (!SORTS.includes(sort)) throw new RangeError(`invalid sort: ${sort}`);
    if (!ORDERS.includes(order)) throw new RangeError(`invalid order: ${order}`);
    if (query.dueBefore !== undefined && !isCalendarDate(query.dueBefore)) {
      throw new RangeError(`invalid dueBefore: ${query.dueBefore}`);
    }
    const tags = (query.tags ?? []).map((tag) => tag.toLowerCase());
    const text = (query.text ?? "").trim().toLowerCase();
    const dueBefore = query.dueBefore;

    const matches = this.todos.filter((todo) => {
      if (status !== "all" && todo.status !== status) return false;
      if (tags.length > 0) {
        const own = new Set(todo.tags.map((tag) => tag.toLowerCase()));
        if (!tags.every((tag) => own.has(tag))) return false;
      }
      if (text !== "" && !todo.title.toLowerCase().includes(text)) return false;
      if (dueBefore !== undefined && (todo.due === null || todo.due > dueBefore)) return false;
      return true;
    });

    const direction = order === "desc" ? -1 : 1;
    return matches.sort((a, b) => {
      let result = 0;
      if (sort === "due") {
        if (a.due === null || b.due === null) {
          result = a.due === b.due ? 0 : a.due === null ? 1 : -1;
        } else {
          result = direction * compare(a.due, b.due);
        }
      } else if (sort === "created") {
        result = direction * compare(a.createdAt, b.createdAt);
      } else if (sort === "title") {
        result = direction * compare(a.title.toLowerCase(), b.title.toLowerCase());
      } else {
        result = direction * compare(a.id, b.id);
      }
      return result !== 0 ? result : a.id - b.id;
    });
  }
}
