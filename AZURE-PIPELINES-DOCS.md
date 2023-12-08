# Azure-pipelines-container

WARNING: This repository is public and therefore should not contain any secrets!!!

## Push to ECR (AMD64)
I you are not on AMD64 this step can take around 3 min, so go get a coffee.
```bash
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/t2e7t6h0
docker buildx create --name amd64 --use
docker buildx use amd64
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 -t analysis-and-design-coursework-public-ecr . --load
docker tag analysis-and-design-coursework-public-ecr:latest public.ecr.aws/t2e7t6h0/analysis-and-design-coursework-public-ecr:latest
docker push public.ecr.aws/t2e7t6h0/analysis-and-design-coursework-public-ecr:latest
```