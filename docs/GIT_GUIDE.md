# Git 分支操作指南（新手版）

这份指南适合本项目的日常开发习惯：

1. 从 `main` 创建一个新分支。
2. 在新分支开发、提交和测试。
3. 功能完善后合并到 `main`。
4. 删除已经完成的新分支。

> 核心原则：`main` 始终保存稳定、可运行的代码。功能没有完成前，不要直接在 `main` 上提交。

## 一、先认识几个概念

| 名称 | 含义 |
| --- | --- |
| `main` | 主分支，保存稳定版本 |
| 功能分支 | 开发某项功能的临时分支，例如 `feature/docker-deploy` |
| 本地分支 | 只存在于自己电脑上的分支 |
| 远端分支 | GitHub 上的分支，例如 `origin/main` |
| `commit` | 给当前改动保存一个版本记录 |
| `push` | 把本地提交上传到 GitHub |
| `pull` | 把 GitHub 上的更新拉到本地 |
| `merge` | 把一个分支的改动合并到另一个分支 |

`origin` 是这个 GitHub 仓库在本地的默认名称。因此：

- `main` 表示本地的主分支。
- `origin/main` 表示 GitHub 上的主分支。

## 二、推荐的完整工作流程

下面以开发“价格提醒”功能为例，分支名使用 `feature/price-alert`。

### 第 1 步：检查当前状态

每次开始操作前都先执行：

```powershell
git status
```

理想状态应该包含：

```text
nothing to commit, working tree clean
```

如果存在未提交改动，先确认这些改动是否应该提交，不要急着切换分支、拉取或合并。

### 第 2 步：更新本地 `main`

```powershell
git switch main
git pull --ff-only origin main
```

`--ff-only` 可以防止 Git 在拉取时意外创建合并提交。命令失败时先检查原因，不要随意使用强制覆盖命令。

### 第 3 步：从最新的 `main` 创建功能分支

```powershell
git switch -c feature/price-alert
```

确认当前分支：

```powershell
git branch --show-current
```

应该输出：

```text
feature/price-alert
```

### 第 4 步：开发并提交改动

开发过程中随时检查：

```powershell
git status
git diff
```

确认改动后提交：

```powershell
git add -A
git commit -m "feat: add price alert"
```

提交说明建议使用简短、明确的英文：

| 类型 | 用途 | 示例 |
| --- | --- | --- |
| `feat` | 新功能 | `feat: add price alert` |
| `fix` | 修复问题 | `fix: correct gold price calculation` |
| `docs` | 修改文档 | `docs: add Git workflow guide` |
| `refactor` | 重构代码 | `refactor: simplify price service` |
| `chore` | 配置或杂项 | `chore: update dependencies` |

一个功能可以提交多次，不需要等全部完成后才提交。每次提交尽量只处理一类改动。

### 第 5 步：把功能分支推送到 GitHub

第一次推送：

```powershell
git push -u origin feature/price-alert
```

`-u` 会建立本地分支和 GitHub 分支的关联。以后在这个分支上可以直接执行：

```powershell
git push
```

### 第 6 步：合并前同步最新的 `main`

如果其他人或自己已经更新了 `main`，先把最新主分支合入功能分支：

```powershell
git status
git fetch origin
git merge origin/main
```

执行前必须确保 `git status` 显示工作区干净。合并后重新运行和测试项目，再推送：

```powershell
git push
```

### 第 7 步：通过 GitHub 合并到 `main`（推荐）

在 GitHub 仓库中创建 Pull Request（PR）：

- `base` 选择 `main`。
- `compare` 选择 `feature/price-alert`。
- 检查改动内容和自动测试。
- 确认无误后点击合并。

使用 PR 的好处是合并前可以再次检查改动，也能在 GitHub 上保留清晰记录。

如果是自己在本地合并，也可以执行：

```powershell
git switch main
git pull --ff-only origin main
git merge --no-ff feature/price-alert
git push origin main
```

不要同时使用 GitHub 合并和本地合并。选择其中一种即可。

### 第 8 步：删除已经合并的功能分支

先更新本地 `main`：

```powershell
git switch main
git pull --ff-only origin main
```

删除本地功能分支：

```powershell
git branch -d feature/price-alert
```

删除 GitHub 上的功能分支：

```powershell
git push origin --delete feature/price-alert
```

最后清理本地保存的远端分支列表：

```powershell
git fetch --prune origin
```

`git branch -d` 会保护尚未合并的分支。如果 Git 提示分支没有合并，先检查原因，不要立即改用 `-D` 强制删除。

## 三、每天最常用的命令清单

```powershell
# 查看当前状态
git status

# 查看当前分支
git branch --show-current

# 查看本地分支及其关联的远端分支
git branch -vv

# 查看最近的提交
git log --oneline --decorate -10

# 查看尚未暂存的具体改动
git diff

# 查看已经暂存、准备提交的改动
git diff --staged

# 暂存并提交全部改动
git add -A
git commit -m "feat: describe the change"

# 推送当前分支
git push
```

## 四、发生冲突时怎么办

出现下面的信息表示发生了冲突：

```text
CONFLICT (content): Merge conflict in README.md
```

先执行：

```powershell
git status
```

冲突文件中通常会出现：

```text
<<<<<<< HEAD
当前分支的内容
=======
要合并进来的内容
>>>>>>> other-branch
```

处理步骤：

1. 用编辑器打开冲突文件。
2. 保留正确内容，并删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记。
3. 保存文件。
4. 使用 `git add` 标记冲突已解决。
5. 完成提交。

```powershell
git add README.md
git commit
```

如果想放弃本次合并，恢复到合并前：

```powershell
git merge --abort
```

### `ours` 和 `theirs` 容易混淆

普通合并时：

- `ours` 是当前所在分支。
- `theirs` 是正在合并进来的分支。

例如，在功能分支执行 `git merge origin/main`：

- `ours` 是功能分支。
- `theirs` 是 `origin/main`。

执行 `git stash apply` 发生冲突时：

- `ours` 是当前分支已有的内容。
- `theirs` 通常是 stash 中保存的本地内容。

不要只根据 `ours` 这个名字判断哪份是自己的文件，先确认当前操作的方向。

## 五、临时保存未完成的改动

优先使用正常提交保存工作。确实不方便提交时，才使用 stash：

```powershell
git stash push -u -m "temporary: price alert work"
```

查看 stash：

```powershell
git stash list
git stash show --stat "stash@{0}"
```

恢复时建议先使用 `apply`，这样 stash 备份仍然保留：

```powershell
git stash apply "stash@{0}"
```

确认恢复成功并完成提交后，再删除 stash：

```powershell
git stash drop "stash@{0}"
```

## 六、常见误操作及恢复方法

### 1. 改了文件，但还没有提交

放弃某个文件尚未暂存的改动：

```powershell
git restore path/to/file
```

这会丢弃该文件的本地改动，执行前必须确认不再需要它。

### 2. 已经 `git add`，但还没有提交

取消暂存，但保留文件内容：

```powershell
git restore --staged path/to/file
```

### 3. 功能误提交到了 `main`，但还没有推送

先从当前提交创建正确的功能分支：

```powershell
git switch -c feature/correct-branch
```

确认新分支已包含提交后，再把本地 `main` 恢复到 GitHub 版本：

```powershell
git switch main
git reset --hard origin/main
```

`reset --hard` 会丢弃目标范围内的本地改动。只有在确认功能提交已由新分支保存、工作区没有其他重要内容时才能执行。

### 4. 功能误提交并推送到了 `main`

不要直接改写已推送的 `main` 历史，也不要强制推送。更安全的做法是：

1. 先保留当前提交到功能分支。
2. 使用 `git revert` 创建一个撤销提交。
3. 将撤销提交推送到 `main`。
4. 之后通过 PR 正常合并功能分支。

这类操作会影响远端主分支。对命令不确定时，先把 `git status`、`git branch -vv` 和 `git log --oneline --decorate -10` 的输出保存下来，再处理。

### 5. 不确定当前处于什么状态

先停止继续输入 Git 命令，依次运行：

```powershell
git status
git branch -vv
git log --oneline --decorate --graph -10
git stash list
```

这些命令只查看状态，不会修改文件。

## 七、推荐的分支命名

| 场景 | 命名方式 | 示例 |
| --- | --- | --- |
| 新功能 | `feature/功能名` | `feature/price-alert` |
| 修复问题 | `fix/问题名` | `fix/incorrect-weight` |
| 文档修改 | `docs/文档名` | `docs/git-guide` |
| 重构 | `refactor/模块名` | `refactor/calculator` |

分支名建议使用小写英文，单词之间用短横线连接。

## 八、操作前后的安全检查

每次提交前：

```powershell
git branch --show-current
git status
git diff --staged
```

重点确认：

- 当前确实位于功能分支，而不是 `main`。
- 暂存区没有密码、密钥、`.env` 等敏感文件。
- 暂存区没有无关文件。
- 项目已经运行或测试过。

每次合并前确认：

- 功能分支的工作区干净。
- 功能分支已经推送到 GitHub。
- 功能已经测试完成。
- PR 的 `base` 是 `main`，`compare` 是功能分支。

每次删除分支前确认：

- PR 已成功合并。
- 本地 `main` 已拉取最新内容。
- `git branch -d` 没有给出未合并警告。

## 九、最简流程速查

```powershell
# 1. 从最新 main 创建功能分支
git switch main
git pull --ff-only origin main
git switch -c feature/my-feature

# 2. 开发并提交
git status
git add -A
git commit -m "feat: add my feature"
git push -u origin feature/my-feature

# 3. 在 GitHub 创建 PR，并合并到 main

# 4. 合并后更新 main 并删除功能分支
git switch main
git pull --ff-only origin main
git branch -d feature/my-feature
git push origin --delete feature/my-feature
git fetch --prune origin
```

遇到不确定的情况时，最重要的不是尝试更多命令，而是先执行 `git status`，看清当前分支和 Git 正在进行的操作。

## 十、让本地分支和 GitHub 保持一致

“保持一致”通常有两种情况：

1. **安全同步**：保留自己的本地提交，只拉取 GitHub 上的新提交。这是日常推荐方式。
2. **以 GitHub 为准**：放弃本地改动和本地提交，让本地内容完全恢复成 GitHub 版本。只有确定本地内容不再需要时才使用。

### 1. 日常安全同步（推荐）

先确认当前是否存在未提交内容：

```powershell
git status
```

如果工作区干净，获取 GitHub 最新分支信息：

```powershell
git fetch --prune origin
```

其中：

- `fetch` 只更新远端信息，不会修改当前文件。
- `--prune` 会清理“GitHub 已删除，但本地还残留记录”的远端分支引用。

然后逐个同步需要使用的分支：

```powershell
# 同步 main
git switch main
git pull --ff-only origin main

# 同步某个功能分支，例如 new
git switch new
git pull --ff-only origin new
```

最后检查本地分支与远端分支的关联：

```powershell
git branch -vv
```

常见状态：

| 显示 | 含义 |
| --- | --- |
| `[origin/main]` | 本地分支与远端分支一致 |
| `[origin/main: ahead 1]` | 本地多一个提交，通常需要 `git push` |
| `[origin/main: behind 1]` | GitHub 多一个提交，通常需要 `git pull --ff-only` |
| `[origin/main: ahead 1, behind 1]` | 两边都有不同提交，需要合并或变基，不能直接快进 |
| `[origin/分支名: gone]` | GitHub 上的对应分支已经删除 |

### 2. GitHub 有分支，但本地没有

先更新远端分支列表：

```powershell
git fetch --prune origin
```

查看全部本地和远端分支：

```powershell
git branch -a
```

创建对应的本地分支并建立跟踪关系：

```powershell
git switch --track origin/分支名
```

例如：

```powershell
git switch --track origin/feature/price-alert
```

### 3. GitHub 已删除分支，但本地仍然存在

先清理远端分支记录：

```powershell
git fetch --prune origin
git branch -vv
```

如果显示 `[origin/分支名: gone]`，并且确认该分支已经合并或不再需要，可以删除本地分支：

```powershell
git branch -d 分支名
```

如果 Git 提示分支尚未合并，先检查分支中的提交，不要立即使用 `-D` 强制删除：

```powershell
git log main..分支名 --oneline
```

### 4. 本地有新提交，需要同步到 GitHub

先确认当前分支：

```powershell
git branch --show-current
git status
```

然后推送：

```powershell
git push
```

如果是第一次推送这个分支，需要建立跟踪关系：

```powershell
git push -u origin 当前分支名
```

### 5. 完全以 GitHub 为准（会丢失本地内容）

只有明确不需要当前分支的本地修改和本地提交时，才能使用下面的命令。

先检查并尽量保存重要内容：

```powershell
git status
git branch --show-current
git log --oneline --decorate -10
```

如果只是临时保留本地内容，可以先创建 stash：

```powershell
git stash push -u -m "backup before syncing with GitHub"
```

然后以 GitHub 上的 `main` 为准覆盖本地 `main`：

```powershell
git fetch --prune origin
git switch main
git reset --hard origin/main
git clean -fd
```

命令影响：

- `git reset --hard origin/main`：丢弃已跟踪文件的本地修改，并丢弃只存在于本地 `main` 的提交。
- `git clean -fd`：删除所有未被 Git 跟踪的文件和目录。

如果要覆盖其他分支，把命令中的分支名一起替换。例如以 GitHub 上的 `new` 为准：

```powershell
git switch new
git reset --hard origin/new
git clean -fd
```

> 警告：不要在没有执行 `git status` 的情况下直接运行 `reset --hard` 或 `clean -fd`。如果只是正常更新代码，使用 `git pull --ff-only` 即可。

### 6. 推荐的同步检查顺序

不确定该使用哪种同步方式时，先执行下面这些只读命令：

```powershell
git status
git branch -vv
git fetch --prune origin
git branch -vv
git log --oneline --decorate --graph -10 --all
```

根据结果判断：

- 显示 `behind`：使用 `git pull --ff-only`。
- 显示 `ahead`：确认提交无误后使用 `git push`。
- 同时显示 `ahead` 和 `behind`：先检查双方提交，再决定合并方式。
- 显示 `gone`：确认分支已经合并后，使用 `git branch -d` 删除本地分支。
- 存在未提交文件：先提交或 stash，再切换、拉取或覆盖分支。
