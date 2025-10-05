param(
  [string]$DeviceId = '11111111-1111-1111-1111-111111111111',
  [Parameter(Mandatory=$true)][string]$Question
)
$body = @{ device_id = $DeviceId; question = $Question } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:18000/ai/chat -Body $body -ContentType 'application/json'
