# TFM_10 — Guía de Git y GitHub para el grupo

> Para trabajar los 5 en el mismo código sin pisarnos. Pensada para quien no ha
> usado Git antes. Raquel Roca · Junio 2026.

---

## Idea en una frase

Git guarda el historial del proyecto y deja que cada uno trabaje en su copia.
GitHub es la nube donde vive la copia común. La regla de oro: **nadie escribe
directo en `main`; todo cambio entra por una rama y un *pull request* (PR)** que
revisa otra persona.

---

## 0. Preparación (una vez por persona)

1. Crear cuenta en https://github.com (con el email de cada una).
2. Instalar Git: https://git-scm.com/download/win  (en Windows incluye "Git Bash").
3. Configurar identidad (en una terminal):
   ```bash
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu-email@ejemplo.com"
   ```
4. Instalar **GitHub Desktop** (https://desktop.github.com) si preferís interfaz
   gráfica en vez de comandos. Es totalmente válido y más fácil para empezar.

---

## 1. Crear el repositorio (lo hace UNA persona, p. ej. Raquel)

1. En GitHub: botón **New repository**.
   - Nombre: `tfm-reconstruccion-3d`
   - **Privado** (es trabajo académico).
   - Marcar "Add a README".
2. **Invitar al grupo**: Settings → Collaborators → añadir a las otras 4 por su
   usuario de GitHub.
3. Subir el `.gitignore` de la sección 5 (¡importante para no subir los datasets!).

---

## 2. Traerse el repo a tu ordenador (cada persona)

```bash
git clone https://github.com/<usuario>/tfm-reconstruccion-3d.git
cd tfm-reconstruccion-3d
```

---

## 3. Flujo de trabajo diario

```bash
# 1. Antes de empezar, traer lo último de main
git checkout main
git pull

# 2. Crear tu rama para la tarea (nombre claro)
git checkout -b etapa2/reconstruccion-nerfacto

# 3. Trabajar, y guardar cambios por trozos
git add .
git commit -m "E2: primer entrenamiento nerfacto sobre 1 taza"

# 4. Subir tu rama a GitHub
git push -u origin etapa2/reconstruccion-nerfacto
```

Luego, en GitHub: botón **Compare & pull request** → describir el cambio →
asignar como revisor al **secundario de tu etapa** → cuando lo aprueba, **Merge**.

> Con GitHub Desktop esto mismo son botones: "Current branch" → "New branch",
> "Commit", "Push", "Create Pull Request".

---

## 4. Convenciones que nos ahorran líos

- **Ramas:** `etapaN/descripcion-corta` (ej. `etapa3/shape-completion-pcn`).
- **Commits:** empezar por la etapa: `"E2: ..."`, `"E4: ..."`, `"docs: ..."`.
- **Un PR = un cambio** con sentido propio; pequeño y revisable.
- **Nunca** hacer `git push --force` sobre `main`.
- Si hay conflicto, **avisad en el grupo** antes de resolver a ciegas.

---

## 5. `.gitignore` (MUY importante: no subir datos pesados)

Los datasets (cientos de MB / GB) **no van a Git**. Crear un fichero `.gitignore`
en la raíz del repo con esto:

```gitignore
# Datos y modelos pesados (viven en HF/Drive, no en Git)
Datos/
Modelos_generados/
*.glb
*.ply
*.stl
*.obj
*.zip
*.binvox

# Python
__pycache__/
*.pyc
.venv/
venv/
.ipynb_checkpoints/

# Sistema / editores
.DS_Store
Thumbs.db
.vscode/
.idea/
```

> ¿Y si necesitamos versionar algún dato grande? Usar **Git LFS**
> (https://git-lfs.com) solo para ficheros concretos, o mejor dejarlos en
> Hugging Face / Drive y enlazarlos desde el README.

---

## 6. Qué SÍ va al repo

- Código (`Scripts/`, notebooks, código de cada etapa).
- Documentación (`Documentacion/*.md`).
- Ficheros de configuración y `requirements.txt`.
- Resultados pequeños (CSV de métricas, figuras para la memoria).

NO van: los datasets, los modelos `.glb/.ply/.stl`, los checkpoints de
entrenamiento. Esos se enlazan, no se suben.
