# Token Manager

### Description

### Freezing the venv and adding new dependencies
If you have set the venv correctly in pycharm, you will not need to run `venv/bin/activate` before running these, since
the terminal in pycharm will automatically do this for you. If it does not, you can enable this by going to 
setting/tools/terminal, and then checking activate virtualenv.
#### What are the dependency files?
This project contains two dependency files, `local_dependencies.txt` is to be used for local development, this includes 
dependencies that are not needed in the deployment, such as `pytest`. This is to reduce costs and deployment time.
`lambda_dependencies.txt` is a more lightweight dependency file only containing what is needed in deployment. _Please
note that some dependencies come with lambda python, such as boto3, so it is unlikely you will need to install anything
to this file._
#### Local development
To install new dependencies, you can do this via the gui in pycharm, by pressing the interpreter button in the bottom 
left of your screen. Then, click the `+` button in the top right of the window that pops up, and search for the package 
you want to install. Note that if you stop using a dependency, you should remove it from this section by pressing the 
`-` button. You can also do this via the command line with this command:
```bash
pip install <package-name>
```
Pycharm will not automatically add dependencies to the `local_dependencies.txt` file, instead you will have to do this
yourself. Please note that this will not add dependencies to the `lambda_dependencies.txt` file.
_AKA, this is only for local development._
```bash
pip freeze > local_dependencies.txt
```
#### Lambda deployment
```bash
mkdir dependencies
pip install -t dependencies -r lambda_dependencies.txt
mkdir out

# if dependencies not empty
if [ "$(ls -A dependencies)" ]; then
    cd dependencies
    zip -r ../out/token_mgr.zip .
    cd ..
fi

zip -r out/token_mgr.zip src
aws s3 cp out/token_mgr.zip s3://analysis-and-design-course-work-lambda-buckets/token_mgr.zip
aws lambda update-function-code --function-name arn:aws:lambda:eu-west-1:203163753194:function:FfSmartAppTheOneWeAreWork-AnalysisAndDesignTokenMg-Iw77qKeVW3Yn --s3-bucket analysis-and-design-course-work-lambda-buckets --s3-key token_mgr.zip 
q
rm -r out
rm -r dependencies
```

### Expected APIs
