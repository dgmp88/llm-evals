import { Kysely, PostgresDialect } from "kysely";
import { Pool } from "pg";

import type { DB } from "./db.d";
import { ENV } from "./env";
const dialect = new PostgresDialect({
  pool: new Pool({
    connectionString: ENV.DATABASE_URL,
  }),
});

export const db = new Kysely<DB>({
  dialect,
});
