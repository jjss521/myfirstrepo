;;; ============================================================
;;; PDSG-LISP 配电系统图自动生成程序 v1.0.0
;;; APPLOAD 加载本文件，然后输入 PDSG_UI 打开图形界面
;;; ============================================================

(setq *pdsg-install-dir*
  (if (and (getvar "DWGPREFIX") (/= (getvar "DWGPREFIX") ""))
    (getvar "DWGPREFIX")
    (if (and (getvar "TEMPPREFIX") (/= (getvar "TEMPPREFIX") ""))
      (getvar "TEMPPREFIX")
      ""
    )
  )
)

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

;;; MODULE: pdsg-main.lsp

;;; ============================================================
;;; PDSG-LISP - 配电系统图自动生成程序
;;; 转换自 PDSG.NET (C# → AutoLISP)
;;; 用于 AutoCAD 运行
;;; ============================================================

;;; 全局变量
(setq *pdsg-version* "1.0.0")
(setq *pdsg-config* nil)
(setq *pdsg-block-catalog* nil)

;;; 布局常量
(setq *pdsg-max-cols* 12)      ; 每行最大回路数
(setq *pdsg-row-height* 80.0)  ; 行间距 (mm)
(setq *pdsg-unit* "mm")        ; 坐标单位

;;; ------------------------------------------------------------
;;; 加载配置（支持简单 key: value 格式）
;;; ------------------------------------------------------------
(defun pdsg-load-config ( / config-file f line key val colon-pos)
  (setq config-file (findfile "pdsg-config.yaml"))
  (if (null config-file)
    (progn
      (princ "\n[WARN] 未找到配置文件 pdsg-config.yaml，使用默认配置")

(princ)
(princ "\n[PDSG-LISP v1.0.0] 输入 PDSG_UI 打开界面")
(princ)
