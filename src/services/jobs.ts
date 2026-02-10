import { redis } from "../config/redis";
import { v4 as uuidv4 } from "uuid";

const queueTailorJobs = async (job: {
    user_id: string;
    vton_id: string;
    uncleaned_outfit_s3: string;
}) => {
    try {
        const jobId = uuidv4();
        const jobData = {
            id: jobId,
            ...job,
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
    user_id: string;
    vton_id: string;
    user_snap_s3: string;
    uncleaned_outfit_s3: string;
}) => {
    try {
        const jobId = uuidv4();
        const jobData = {
            id: jobId,
            ...job,
            created_at: new Date().toISOString(),
        };
        await redis.lpush("queue:weaver_jobs", JSON.stringify(jobData));
        return jobId;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

const queueService = {
    queueTailorJobs,
    queueWeaverJobs,
}

export default queueService;