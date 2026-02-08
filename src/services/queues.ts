import { redis } from "../config/redis";
import { v4 as uuidv4 } from "uuid";

export const queueTailorJobs = async (job: any) => {
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

export const queueWeaverJobs = async (job: any) => {
    try {
        const jobId = uuidv4();
        const jobData = {
            jobId,
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