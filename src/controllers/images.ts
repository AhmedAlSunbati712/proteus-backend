import imageService from "../services/images";
import { Request, Response } from "express";

const getPresignedUploadUrl = async (req: Request, res: Response): Promise<void> => {
    try {
        const { userId, fileType, fileName } = req.body;
        const { url, key } = await imageService.getPresignedUploadUrl(userId, fileType, fileName);
        res.json({ url, key });
    } catch (error) {
        res.status(500).json({ error: "Failed to get presigned upload URL" });
    }
};

const getPresignedDownloadUrl = async (req: Request, res: Response): Promise<void> => {
    try {
        const { userId, fileType, fileName } = req.body;
        const url = await imageService.getPresignedDownloadUrl(userId, fileType, fileName);
        res.json({ url });
    } catch (error) {
        res.status(500).json({ error: "Failed to get presigned download URL" });
    }
};

const imageController = {
    getPresignedUploadUrl,
    getPresignedDownloadUrl,
};
export default imageController;