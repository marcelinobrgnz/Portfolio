# Verify no billable AWS demo resources remain (eu-west-1)
$ErrorActionPreference = "Continue"
$Region = "eu-west-1"
$ReportFile = "D:\IIMA\Portfolio\demo-proof\AWS_TEARDOWN_VERIFICATION.md"

function Check($name, $cmd) {
  $out = Invoke-Expression $cmd 2>&1 | Out-String
  $clean = $out.Trim()
  if (-not $clean -or $clean -eq "None" -or $clean -eq "[]" -or $clean -eq "{}") {
    return @{ name = $name; status = "CLEAR"; detail = "(none)" }
  }
  return @{ name = $name; status = "FOUND"; detail = $clean }
}

$checks = @(
  (Check "ECS clusters" "aws ecs list-clusters --region $Region --query clusterArns --output text")
  (Check "ECR repositories" "aws ecr describe-repositories --region $Region --query 'repositories[].repositoryName' --output text")
  (Check "CloudWatch log groups" "aws logs describe-log-groups --log-group-name-prefix /ecs/ --region $Region --query 'logGroups[].logGroupName' --output text")
  (Check "Demo security group" "aws ec2 describe-security-groups --filters Name=group-name,Values=portfolio-wine-api-demo-sg --region $Region --query 'SecurityGroups[].GroupId' --output text")
)

$s3 = aws s3 ls s3://mlops-inference-platform-864981752170/ --region $Region 2>&1 | Out-String
$billable = $checks | Where-Object { $_.status -eq "FOUND" }

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# AWS Teardown Verification")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("Generated: $((Get-Date).ToUniversalTime().ToString('o')) UTC")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Billable compute (should all be CLEAR)")
[void]$sb.AppendLine("")

foreach ($c in $checks) {
  $icon = if ($c.status -eq "CLEAR") { "OK" } else { "WARN" }
  [void]$sb.AppendLine("- [$icon] **$($c.name):** $($c.status) - $($c.detail)")
}

[void]$sb.AppendLine("")
[void]$sb.AppendLine("## S3 kept on purpose (storage only, under 2 USD/mo)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("$(($s3.Trim()))")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("## Expected ongoing cost")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("| Resource | Monthly |")
[void]$sb.AppendLine("|----------|---------|")
[void]$sb.AppendLine("| S3 artifacts | under 2 USD |")
[void]$sb.AppendLine("| ECS / Fargate / ECR | 0 USD |")
[void]$sb.AppendLine("| SageMaker | 0 USD |")
[void]$sb.AppendLine("")

if ($billable.Count -eq 0) {
  [void]$sb.AppendLine("**Result: No active compute billing from this demo.**")
} else {
  [void]$sb.AppendLine("**Result: $($billable.Count) resource(s) still present.**")
}

$text = $sb.ToString()
$text | Set-Content $ReportFile -Encoding UTF8
Write-Host $text
