import jobService from "src/services/jobs";
import { Request, Response } from "express";

const createWeaverJob = async (req: Request & {userId: string}, res: Response) => {
    try {
        const { userId, vton_id, user_snap_s3, uncleaned_outfit_s3 } = req.body;
        if (userId !== req.userId) {
            return res.status(403).json({ error: "Unauthorized" });
        }
        const jobId = await jobService.queueWeaverJobs({ userId, vton_id, user_snap_s3, uncleaned_outfit_s3 });
        res.status(200).json({ jobId });

    } catch (error) {
        res.status(500).json({ error: "Failed to enqueue VTON task" });
    }
}

const createTailorJob = async (req: Request & {userId: string}, res: Response) => {
    try {
        const { userId, vton_id, uncleaned_outfit_s3 } = req.body;
        if (userId !== req.userId) {
            return res.status(403).json({ error: "Unauthorized" });
        }
        const jobId = await jobService.queueTailorJobs({ userId, vton_id, uncleaned_outfit_s3 });
        res.status(200).json({ jobId });

    } catch (error) {
        res.status(500).json({ error: "Failed to enqueue Tailor task" });
    }
}

const jobController = {
    createWeaverJob,
    createTailorJob,
}

export default jobController;