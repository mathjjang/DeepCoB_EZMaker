# PowerShell script to compile all .py files in the lib folder to .mpy files

# Convert relative paths to absolute paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$libPath = Join-Path -Path $scriptPath -ChildPath "source\lib"
$libPath = Resolve-Path $libPath

# Path to mpy-cross executable - adjust based on your installation
$mpyCross = "mpy-cross"

# Path where mpy files will be moved to
$mpyDestPath = Join-Path -Path $scriptPath -ChildPath "mpy\lib"

# Find all .py files
$pyFiles = Get-ChildItem -Path $libPath -Filter "*.py" -Recurse

Write-Host "Found $($pyFiles.Count) Python files to compile"

foreach ($file in $pyFiles) {
    Write-Host "Compiling $($file.FullName)"
    
    try {
        # Run mpy-cross on each file
        & $mpyCross $file.FullName
        
        # Check if compilation was successful
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Success: Created $($file.DirectoryName)\$($file.BaseName).mpy" -ForegroundColor Green
        } else {
            Write-Host "  Failed to compile $($file.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

Write-Host "Compilation complete" -ForegroundColor Cyan 

# Move .mpy files to mpy/lib folder
Write-Host "Moving .mpy files to $mpyDestPath" -ForegroundColor Cyan

# Create destination directory if it doesn't exist
if (-not (Test-Path -Path $mpyDestPath)) {
    New-Item -ItemType Directory -Path $mpyDestPath -Force | Out-Null
    Write-Host "Created directory: $mpyDestPath" -ForegroundColor Yellow
}

# Find all .mpy files in lib folder
$mpyFiles = Get-ChildItem -Path $libPath -Filter "*.mpy" -Recurse

Write-Host "Found $($mpyFiles.Count) .mpy files to move"

foreach ($file in $mpyFiles) {
    # Get the relative path from lib folder properly
    $relPath = $file.FullName.Substring($libPath.ToString().TrimEnd('\').Length)
    $destFile = Join-Path -Path $mpyDestPath -ChildPath $relPath
    $destDir = Split-Path -Path $destFile -Parent
    
    # Create destination directory if it doesn't exist
    if (-not (Test-Path -Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        Write-Host "  Created directory: $destDir" -ForegroundColor Yellow
    }
    
    # Move the file to destination
    try {
        Move-Item -Path $file.FullName -Destination $destFile -Force
        Write-Host "  Moved: $($file.Name) -> $destFile" -ForegroundColor Green
    }
    catch {
        Write-Host "  Error moving file $($file.Name): $_" -ForegroundColor Red
    }
}

Write-Host "File movement complete" -ForegroundColor Cyan 

# --------------------------------------------------------------------
# 추가: config.py와 main.py 는 컴파일하지 않고 그대로 mpy 루트로 복사
# --------------------------------------------------------------------

# mpy 루트 경로 (보드 루트에 올라갈 파일 위치)
$mpyRootPath = Join-Path -Path $scriptPath -ChildPath "mpy"

# mpy 루트 디렉터리 생성
if (-not (Test-Path -Path $mpyRootPath)) {
    New-Item -ItemType Directory -Path $mpyRootPath -Force | Out-Null
    Write-Host "Created mpy root directory: $mpyRootPath" -ForegroundColor Yellow
}

# source/config.py 복사
$configSrc = Join-Path -Path $scriptPath -ChildPath "source\config.py"
if (Test-Path -Path $configSrc) {
    $configDest = Join-Path -Path $mpyRootPath -ChildPath "config.py"
    Copy-Item -Path $configSrc -Destination $configDest -Force
    Write-Host "Copied config.py to $configDest" -ForegroundColor Green
} else {
    Write-Host "Warning: source\config.py not found. Skipping copy." -ForegroundColor Yellow
}

# source/main.py 복사
$mainSrc = Join-Path -Path $scriptPath -ChildPath "source\main.py"
if (Test-Path -Path $mainSrc) {
    $mainDest = Join-Path -Path $mpyRootPath -ChildPath "main.py"
    Copy-Item -Path $mainSrc -Destination $mainDest -Force
    Write-Host "Copied main.py to $mainDest" -ForegroundColor Green
} else {
    Write-Host "Warning: source\main.py not found. Skipping copy." -ForegroundColor Yellow
}