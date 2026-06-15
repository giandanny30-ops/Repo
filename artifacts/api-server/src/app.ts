import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import path from "path";
import fs from "fs";
import router from "./routes";
import iconsRouter from "./routes/icons";
import welcomeCardRouter from "./routes/welcome-card";
import gamesPlayRouter from "./routes/games-play";
import { logger } from "./lib/logger";
import { authMiddleware } from "./middleware/auth.js";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Public routes — no auth required
app.use(iconsRouter);
app.use(welcomeCardRouter);
app.use("/api", gamesPlayRouter);

app.use("/api", authMiddleware, router);

// Serve static bot-panel in production
const staticDir = path.join(process.cwd(), "public");
if (fs.existsSync(staticDir)) {
  app.use(express.static(staticDir));
  app.use((_req, res) => {
    res.sendFile(path.join(staticDir, "index.html"));
  });
}

export default app;
