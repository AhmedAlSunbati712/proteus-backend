import { Router } from "express";
import imageController from "../controllers/images";

const router = Router();

router.get("/presignedUploadUrl", imageController.getPresignedUploadUrl);
router.get("/presignedDownloadUrl", imageController.getPresignedDownloadUrl);

export default router;