import { S3Client } from "@aws-sdk/client-s3";
import dotenv from "dotenv";
dotenv.config();

const AWS_REGION = process.env.AWS_REGION ?? "us-east-1";
const S3_BUCKET = process.env.S3_BUCKET ?? "proteus-bucket";
const isDev = process.env.NODE_ENV === "development";
const MINIO_ENDPOINT = process.env.MINIO_ENDPOINT;

const s3ClientConfig = isDev
  ? {
      region: AWS_REGION,
      endpoint: MINIO_ENDPOINT ? new URL(MINIO_ENDPOINT).href : undefined,
      forcePathStyle: true,
      credentials: {
        accessKeyId: process.env.MINIO_ROOT_USER ?? "",
        secretAccessKey: process.env.MINIO_ROOT_PASSWORD ?? "",
      },
    }
  : {
      region: AWS_REGION,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID ?? "",
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY ?? "",
      },
    };

const s3Client = new S3Client(s3ClientConfig);

export { s3Client, S3_BUCKET };