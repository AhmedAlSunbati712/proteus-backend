import { Router, Response, Request } from "express";
import imageController from "../controllers/images";
import authenticationMiddleware from "src/middleware/auth";

const router = Router();

router.post("/presignedUploadUrl", authenticationMiddleware, async (req, res) => {
    await imageController.getPresignedUploadUrl(req as Request & {userId: string}, res as Response);
});
router.post("/presignedDownloadUrl", authenticationMiddleware, imageController.getPresignedDownloadUrl);

export default router;