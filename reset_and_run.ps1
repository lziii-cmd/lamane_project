Write-Host "🔄 Suppression de l'ancienne base de données (si elle existe)..."
Remove-Item db.sqlite3 -ErrorAction SilentlyContinue

Write-Host "🧹 Suppression des anciennes migrations..."
Get-ChildItem -Recurse -Include "migrations" | Where-Object { $_.PSIsContainer } | ForEach-Object {
    Remove-Item "$($_.FullName)\*.py" -Force -ErrorAction SilentlyContinue
    Remove-Item "$($_.FullName)\*.pyc" -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Migrations supprimées dans $($_.FullName)"
}

Write-Host "🛠️ Génération des nouvelles migrations..."
python manage.py makemigrations

Write-Host "📦 Application des migrations..."
python manage.py migrate

Write-Host "🚀 Démarrage du serveur..."
python manage.py runserver
