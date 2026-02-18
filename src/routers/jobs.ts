import jobController from "src/controllers/jobs";
import authenticationMiddleware from "src/middleware/auth";
import { Router } from "express";
import { Request, Response } from "express";

const router = Router();

router.post("/weaver", authenticationMiddleware, async (req, res) => {
    await jobController.createWeaverJob(req as Request & { userId: string }, res);
});
router.post("/tailor", authenticationMiddleware, async (req, res) => {
    await jobController.createTailorJob(req as Request & { userId: string }, res);
});

export default router;