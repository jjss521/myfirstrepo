;;; ============================================================
;;; PDSG-LISP 统一加载器
;;; 一键加载所有模块，自动打开图形界面
;;; ============================================================

;;; 设置安装目录（从当前文件位置推断）
;;; 当通过 load 加载本文件时，自动获取所在目录
(setq *pdsg-install-dir*
  (cond
    ((getvar "DWGPREFIX"))     ; 当前图纸目录
    ((getvar "TEMPPREFIX"))     ; 临时目录
    ("")                        ; 空
  )
)

;;; 手动设置安装目录命令
(defun c:PDSG_SETDIR ( / dir)
  (setq dir (getstring T "\n请输入 PDSG-LISP 安装目录: "))
  (if (and dir (/= dir ""))
    (progn
      (setq *pdsg-install-dir* dir)
      (princ (strcat "\n[INFO] 安装目录已设置: " dir))
    )
  )
  (princ)
)

;;; 加载单个模块
(defun pdsg-load-module (module-name / full-path)
  (setq full-path (strcat *pdsg-install-dir* module-name))
  (if (findfile full-path)
    (progn
      (load full-path)
      (princ (strcat "\n  [OK] " module-name))
      T
    )
    (progn
      (princ (strcat "\n  [SKIP] " module-name " (未找到: " full-path ")"))
      nil
    )
  )
)

;;; 统一加载所有模块
(defun c:PDSG_INIT ( / success)
  (princ "\n========================================")
  (princ "\n  PDSG-LISP 初始化加载")
  (princ "\n========================================")
  (princ (strcat "\n安装目录: " *pdsg-install-dir*))

  (princ "\n\n加载模块:")

  (pdsg-load-module "pdsg-main.lsp")
  (pdsg-load-module "pdsg-excel.lsp")
  (pdsg-load-module "pdsg-blocks.lsp")
  (pdsg-load-module "pdsg-drawing.lsp")
  (pdsg-load-module "pdsg-ui.lsp")

  (princ "\n\n========================================")
  (princ "\n  加载完成！")
  (princ "\n========================================")

  (princ "\n输入 PDSG_UI 打开图形界面")
  (princ)
)

;;; 自动加载提示
(princ (strcat "\n[PDSG-LISP 加载器就绪] 安装目录: " *pdsg-install-dir*))
(princ "\n输入 PDSG_INIT 初始化并打开图形界面")
(princ "\n输入 PDSG_SETDIR 手动设置安装目录")
(princ)
