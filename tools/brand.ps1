# Generate the community integration icon. This is not an official Pentek logo.
Add-Type -AssemblyName System.Drawing
$outDir = Join-Path $PSScriptRoot '..\custom_components\pentek_intellidrive\brand'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

foreach ($size in @(256, 512)) {
    $bitmap = [Drawing.Bitmap]::new($size, $size)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    $drop = [Drawing.Drawing2D.GraphicsPath]::new()
    $background = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(15, 110, 160))
    $highlight = [Drawing.Pen]::new([Drawing.Color]::FromArgb(160, 220, 240), 9)
    try {
        $graphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.Clear([Drawing.Color]::Transparent)
        $graphics.ScaleTransform(($size / 256.0), ($size / 256.0))
        $graphics.FillEllipse($background, 8, 8, 240, 240)
        $drop.AddBezier(128, 44, 116, 77, 74, 109, 74, 146)
        $drop.AddBezier(74, 146, 74, 216, 182, 216, 182, 146)
        $drop.AddBezier(182, 146, 182, 109, 140, 77, 128, 44)
        $drop.CloseFigure()
        $graphics.FillPath([Drawing.Brushes]::White, $drop)
        $highlight.StartCap = [Drawing.Drawing2D.LineCap]::Round
        $highlight.EndCap = [Drawing.Drawing2D.LineCap]::Round
        $graphics.DrawArc($highlight, 91, 124, 72, 65, 75, 90)
        $filename = if ($size -eq 256) { 'icon.png' } else { 'icon@2x.png' }
        $bitmap.Save((Join-Path $outDir $filename), [Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $highlight.Dispose()
        $background.Dispose()
        $drop.Dispose()
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}
