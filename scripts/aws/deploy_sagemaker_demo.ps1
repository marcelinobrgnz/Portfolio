# SageMaker deploy — delegates to AWS CodeBuild path (no local Docker required)
& "$PSScriptRoot\deploy_sagemaker_aws.ps1" @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
