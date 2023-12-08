# ECS
## Description


## Running the project
To run the project you need to have docker installed.
You will need to have aws cli setup with the correct permissions.
You can run the project with the following commands:
```bash
docker build -t analysis-and-design-coursework-ecs .
```
```bash
docker run -p 4000:80 -e "DYNAMODB_TABLE=analysis-and-design-ecs-session-table" -e "FRIDGE_MGR_ARN=arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignFridgeM-JGnzKOPDBYoi" -e "ORDER_MGR_ARN=arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignOrdersM-Q5wAIRISq5SD" -e "USER_MGR_ARN=arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignUsersMg-AzDLX5oyzz1y" -e "HEALTH_REPORT_MGR_ARN=arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignHealthR-Fhf8nl7TD4Dl" -e "TOKEN_MGR_ARN=arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignTokenMg-Iw77qKeVW3Yn" analysis-and-design-coursework-ecs
```
Open your browser and go to http://localhost:4000.
If running on an ECS you will still use port 4000 but the url will be different.

## Push to ECR
_Note: this must be build for arm processors_
```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 203163753194.dkr.ecr.eu-west-1.amazonaws.com
docker build -t analysis-and-design-coursework-private-ecr .
docker tag analysis-and-design-coursework-private-ecr:latest 203163753194.dkr.ecr.eu-west-1.amazonaws.com/analysis-and-design-coursework-private-ecr:latest
docker push 203163753194.dkr.ecr.eu-west-1.amazonaws.com/analysis-and-design-coursework-private-ecr:latest
```