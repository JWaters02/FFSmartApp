# Create directories
New-Item -ItemType Directory -Path "dependencies", "out" -Force

# Install dependencies
pip install -t dependencies -r lambda_dependencies.txt

# Zip dependencies if the directory is not empty
if (Test-Path dependencies/*) {
    Compress-Archive -Path dependencies/* -DestinationPath out/orders_mgr.zip
}

# Change to the src directory to zip its contents without including 'src\' in the paths
Push-Location -Path src
Get-ChildItem -Path . | Compress-Archive -DestinationPath ../out/orders_mgr.zip -Update
Pop-Location

# AWS S3 and Lambda commands
aws s3 cp out/orders_mgr.zip s3://analysis-and-design-course-work-lambda-buckets/orders_mgr.zip
aws lambda update-function-code --function-name arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignOrdersM-Q5wAIRISq5SD --s3-bucket analysis-and-design-course-work-lambda-buckets --s3-key orders_mgr.zip

# Clean up
Remove-Item -Recurse -Force out, dependencies
