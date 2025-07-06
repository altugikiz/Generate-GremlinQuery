# PowerShell script to test the production API
$headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

# Test 1: Semantic Gremlin Translation
Write-Host "🧪 Testing Semantic Gremlin Translation..." -ForegroundColor Cyan
$body = @{
    query = "Türkiye otellerinin isimlerini göster"
    max_results = 5
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/semantic/gremlin" -Method POST -Headers $headers -Body $body
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Generated Query: $($response.gremlin_query)" -ForegroundColor Yellow
    Write-Host "Execution Time: $($response.execution_time_ms)ms" -ForegroundColor Blue
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Execute Gremlin Query
Write-Host "`n🧪 Testing Gremlin Execution..." -ForegroundColor Cyan
$body2 = @{
    query = "g.V().hasLabel('Hotel').limit(3).valueMap('hotel_name')"
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/semantic/execute" -Method POST -Headers $headers -Body $body2
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Results Count: $($response2.results_count)" -ForegroundColor Yellow
    Write-Host "Execution Time: $($response2.execution_time_ms)ms" -ForegroundColor Blue
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Semantic Ask
Write-Host "`n🧪 Testing Semantic Ask..." -ForegroundColor Cyan
$body3 = @{
    query = "Hangi otellerde temizlik problemi var?"
    max_results = 5
} | ConvertTo-Json

try {
    $response3 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/semantic/ask" -Method POST -Headers $headers -Body $body3
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "Answer Length: $($response3.answer.Length) characters" -ForegroundColor Yellow
    Write-Host "Execution Time: $($response3.execution_time_ms)ms" -ForegroundColor Blue
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Production API Testing Complete!" -ForegroundColor Green
