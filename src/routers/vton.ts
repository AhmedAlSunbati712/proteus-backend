import vtonController from "src/controllers/vton";
import authenticationMiddleware from "src/middleware/auth";
import { Router } from "express";
import { Request, Response } from "express";

const router = Router();

router.get("/", authenticationMiddleware, async (req, res) => {
    await vtonController.getVTONs(req as Request & { user_id: string }, res);
});
router.post("/", authenticationMiddleware, async (req, res) => {
    await vtonController.createVTON(req as Request & { user_id: string }, res);
});
router.put("/:id", authenticationMiddleware, async (req, res) => {
    await vtonController.updateVTON(req as Request & { user_id: string }, res);
});
router.delete("/:id", authenticationMiddleware, async (req, res) => {
    await vtonController.deleteVTON(req as Request & { user_id: string }, res);
});

export default router;
