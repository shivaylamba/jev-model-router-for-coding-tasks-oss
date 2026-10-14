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
}
