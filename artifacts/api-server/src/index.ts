import app from "./app";
import { logger } from "./lib/logger";

const rawPort = process.env["PORT"];

if (!rawPort) {
  throw new Error(
    "PORT environment variable is required but was not provided.",
  );
}

const port = Number(rawPort);

if (Number.isNaN(port) || port <= 0) {
  throw new Error(`Invalid PORT value: "${rawPort}"`);
}

async function runMigration() {
  if (!process.env["DATABASE_URL"]) {
    logger.warn("DATABASE_URL not set — skipping DB migration, using in-memory defaults");
    return;
  }
  try {
    const { pool } = await import("@workspace/db");
    await pool.query(`
      CREATE TABLE IF NOT EXISTS embeds (
        name        TEXT PRIMARY KEY,
        data        JSONB NOT NULL,
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `);
    logger.info("DB migration OK — embeds table ready");
  } catch (err) {
    logger.error({ err }, "DB migration failed — server will start but embeds may not persist");
  }
}

process.on("uncaughtException", (err) => {
  logger.error({ err }, "uncaughtException — keeping process alive");
});

process.on("unhandledRejection", (reason) => {
  logger.error({ reason }, "unhandledRejection — keeping process alive");
});

runMigration().then(async () => {
  if (process.env["DATABASE_URL"]) {
    try {
      const { pool } = await import("@workspace/db");
      pool.on("error", (err) => {
        logger.error({ err }, "pg pool idle client error — connection will be replaced");
      });
    } catch (_) {}
  }

  app.listen(port, (err) => {
    if (err) {
      logger.error({ err }, "Error listening on port");
      process.exit(1);
    }
    logger.info({ port }, "Server listening");
  });
});
