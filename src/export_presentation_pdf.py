from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs'
PPTX = OUTPUT / 'sunum_TASLAK.pptx'
PDF = OUTPUT / 'sunum_TASLAK.pdf'

POWERSHELL_SCRIPT = r'''param([string]$SourcePath, [string]$TargetPath)
$ErrorActionPreference = 'Stop'
$app = $null
$presentation = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $presentation = $app.Presentations.Open($SourcePath, 0, 0, 1)
    $presentation.SaveAs($TargetPath, 32)
    $presentation.Close()
    $presentation = $null
    $app.Quit()
    $app = $null
    if (-not (Test-Path $TargetPath)) { throw 'PDF dosyası oluşmadı.' }
    Write-Output "Presentation PDF created: $TargetPath"
    exit 0
} catch {
    Write-Error $_
    if ($presentation -ne $null) { try { $presentation.Close() } catch {} }
    if ($app -ne $null) { try { $app.Quit() } catch {} }
    exit 1
}
'''

def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not PPTX.exists():
        print(f'WARNING: Sunum dosyası bulunamadı: {PPTX}')
        return 0

    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if soffice:
        result = subprocess.run(
            [soffice, '--headless', '--convert-to', 'pdf', '--outdir', str(OUTPUT), str(PPTX)],
            cwd=ROOT, capture_output=True, text=True
        )
        if result.returncode == 0 and PDF.exists() and PDF.stat().st_mtime >= PPTX.stat().st_mtime - 2:
            print(f'Presentation PDF created: {PDF}')
            return 0
        if result.stdout.strip(): print(result.stdout.strip())
        if result.stderr.strip(): print(result.stderr.strip())

    # On Windows, try the installed Microsoft PowerPoint COM interface without changing security settings.
    if os.name == 'nt' and (shutil.which('powershell') or shutil.which('powershell.exe')):
        powershell = shutil.which('powershell') or shutil.which('powershell.exe')
        script_path = None
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.ps1', encoding='utf-8', delete=False) as f:
                f.write(POWERSHELL_SCRIPT)
                script_path = f.name
            result = subprocess.run(
                [powershell, '-NoProfile', '-File', script_path, str(PPTX), str(PDF)],
                cwd=ROOT, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and PDF.exists():
                print(f'Presentation PDF created: {PDF}')
                return 0
            if result.stdout.strip(): print(result.stdout.strip())
            if result.stderr.strip(): print(result.stderr.strip())
        except Exception as exc:
            print(f'PowerPoint otomatik PDF dışa aktarımı yapılamadı: {exc}')
        finally:
            if script_path:
                try: Path(script_path).unlink(missing_ok=True)
                except Exception: pass

    if PDF.exists() and PDF.stat().st_mtime >= PPTX.stat().st_mtime:
        print(f'Presentation PDF already exists: {PDF}')
        return 0
    print('UYARI: PPTX üretildi ancak güncel sunum PDF otomatik dışa aktarılamadı.')
    print('PowerPoint: outputs/sunum_TASLAK.pptx dosyasını aç > File > Export / Save As > PDF seç.')
    # Do not fail the full analysis pipeline because no PDF converter is installed.
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
