import { pgTable, text, jsonb, timestamp } from "drizzle-orm/pg-core";

export const embedsTable = pgTable("embeds", {
  name: text("name").primaryKey(),
  data: jsonb("data").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export type EmbedRow = typeof embedsTable.$inferSelect;
