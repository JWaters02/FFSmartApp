# Create directories
New-Item -ItemType Directory -Path "dependencies", "out" -Force

# Install dependencies
pip install -t dependencies -r .\lambda_dependencies.txt

# Zip dependencies if the directory is not empty
if (Test-Path dependencies/*) {
    Compress-Archive -Path dependencies/* -DestinationPath out/users_mgr.zip
}

# Change to the src directory to zip its contents without including 'src\' in the paths
Push-Location -Path src
Get-ChildItem -Path . | Compress-Archive -DestinationPath ../out/users_mgr.zip -Update
Pop-Location

# AWS S3 and Lambda commands
aws s3 cp out/users_mgr.zip s3://analysis-and-design-course-work-lambda-buckets/users_mgr.zip
aws lambda update-function-code --function-name arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignUsersMg-AzDLX5oyzz1y --s3-bucket analysis-and-design-course-work-lambda-buckets --s3-key users_mgr.zip

# Clean up
Remove-Item -Recurse -Force out, dependencies