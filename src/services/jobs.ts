import { redis } from "../config/redis";
import { v4 as uuidv4 } from "uuid";

const queueTailorJobs = async (job: {
    userId: string;
    vton_id: string;
    uncleaned_outfit_s3: string;
}) => {
    try {
        const jobId = uuidv4();
        const jobData = {
            id: jobId,
            user_id: job.userId,
            vton_id: job.vton_id,
            uncleaned_outfit_s3: job.uncleaned_outfit_s3,
            created_at: new Date().toISOString(),
        };
        await redis.lpush("queue:tailor_jobs", JSON.stringify(jobData));
        return jobId;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

const queueWeaverJobs = async (job: {
    userId: string;
    vton_id: string;
    user_snap_s3: string;
    uncleaned_outfit_s3: string;
}) => {
    try {
        const jobId = uuidv4();
        const jobData = {
            id: jobId,
            user_id: job.userId,
            vton_id: job.vton_id,
            user_snap_s3: job.user_snap_s3,
            uncleaned_outfit_s3: job.uncleaned_outfit_s3,
            created_at: new Date().toISOString(),
        };
        await redis.lpush("queue:weaver_jobs", JSON.stringify(jobData));
        return jobId;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

const jobService = {
    queueTailorJobs,
    queueWeaverJobs,
}

export default jobService;
