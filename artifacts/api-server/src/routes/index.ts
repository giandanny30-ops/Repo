import { Router, type IRouter } from "express";
import healthRouter from "./health";
import authRouter from "./auth";
import commandsRouter from "./commands";
import embedsRouter from "./embeds";
import settingsRouter from "./settings";
import discordRouter from "./discord";
import channelConfigsRouter from "./channel-configs";
import protectionRouter from "./protection";
import gamesRouter from "./games";

const router: IRouter = Router();

// Public routes (no auth required)
router.use(healthRouter);
router.use(authRouter);

// All remaining routes are protected by authMiddleware (applied in app.ts)
router.use(commandsRouter);
router.use(embedsRouter);
router.use(settingsRouter);
router.use(discordRouter);
router.use(channelConfigsRouter);
router.use(protectionRouter);
router.use(gamesRouter);

export default router;
