import imageService from "../services/images";
import { Request, Response } from "express";

const getPresignedUploadUrl = async (req: Request & {userId: string}, res: Response): Promise<void> => {
    try {
        const { fileType, fileName } = req.body;
        if (!fileType || !fileName) {
            res.status(400).json({message: "Filename and file type are required!"});
            return;
        }
        const userId = req.userId;
        const { url, key } = await imageService.getPresignedUploadUrl(userId, fileType, fileName);
        res.json({ url, key });
    } catch (error) {
        res.status(500).json({ error: "Failed to get presigned upload URL" });
    }
};

const getPresignedDownloadUrl = async (req: Request, res: Response): Promise<void> => {
    try {
        const { key } = req.body;
        if (!key) {
            res.status(400).json({ message: "Key is required" });
            return;
        }
        const url = await imageService.getPresignedDownloadUrl(key);
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