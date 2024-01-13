# ECS
## Description

## Running the project
There are two ways to run the project:
1. Local development server - very fast to start up, but does not have the same environment as the ECS. Use this for quick testing, as it has hot reloading.
2. ECS docker container - slower to start up, but has the same environment as the ECS. Test this before pushing a big change.

### Local development server
First make sure you are inside the src\ecs directory, then run the following commands in order:
#### Windows (assumes you are not using pycharm)
```bash
python -m venv venv
.\venv\Scripts\activate # for window
source venv/bin/activate # for linux/mac
pip install -r .\requirements.txt
flask run --host=0.0.0.0 --port=80 --debug
```
#### Unix (assumes you have got pycharm properly setup) 
```bash
export DYNAMODB_TABLE="analysis-and-design-ecs-session-table"
export FRIDGE_MGR_NAME="FfSmartAppTheOneWeAreWork-AnalysisAndDesignFridgeM-JGnzKOPDBYoi"
export ORDERS_MGR_NAME="FfSmartAppTheOneWeAreWork-AnalysisAndDesignOrdersM-Q5wAIRISq5SD"
export USERS_MGR_NAME="FfSmartAppTheOneWeAreWork-AnalysisAndDesignUsersMg-AzDLX5oyzz1y"
export HEALTH_REPORT_MGR_NAME="FfSmartAppTheOneWeAreWork-AnalysisAndDesignHealthR-Fhf8nl7TD4Dl"
export TOKEN_MGR_NAME="FfSmartAppTheOneWeAreWork-AnalysisAndDesignTokenMg-Iw77qKeVW3Yn"
flask run --host=0.0.0.0 --port=80 --debug
```

### ECS docker container
To run the project you need to have docker installed (docker desktop for windows).
You will need to have aws cli setup with the correct permissions.
You can run the project with the following commands:
```bash
docker build -t analysis-and-design-coursework-ecs .
docker run -p 4000:80 -e "DYNAMODB_TABLE=analysis-and-design-ecs-session-table" -e "FRIDGE_MGR_NAME=FfSmartAppTheOneWeAreWork-AnalysisAndDesignFridgeM-JGnzKOPDBYoi" -e "ORDERS_MGR_NAME=FfSmartAppTheOneWeAreWork-AnalysisAndDesignOrdersM-Q5wAIRISq5SD" -e "USERS_MGR_NAME=FfSmartAppTheOneWeAreWork-AnalysisAndDesignUsersMg-AzDLX5oyzz1y" -e "HEALTH_REPORT_MGR_NAME=FfSmartAppTheOneWeAreWork-AnalysisAndDesignHealthR-Fhf8nl7TD4Dl" -e "TOKEN_MGR_NAME=FfSmartAppTheOneWeAreWork-AnalysisAndDesignTokenMg-Iw77qKeVW3Yn" analysis-and-design-coursework-ecs

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