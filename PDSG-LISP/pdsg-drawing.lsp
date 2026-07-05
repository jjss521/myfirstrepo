;;; ============================================================
;;; PDSG-LISP 绘图工具模块
;;; 提供绘图辅助函数
;;; ============================================================

;;; ------------------------------------------------------------
;;; 图层管理
;;; ------------------------------------------------------------
(defun pdsg-create-layer (layer-name color lineweight /)
  (if (null (tblsearch "LAYER" layer-name))
    (progn
      (command "_.LAYER" "_Make" layer-name "_Color" (itoa color) layer-name "")
      (princ (strcat "\n[INFO] 创建图层: " layer-name))
    )
  )
)

(defun pdsg-setup-layers ()
  (princ "\n=== 初始化图层 ===")
  (pdsg-create-layer "BUS" 1 50)        ; 母线 - 红色
  (pdsg-create-layer "CIRCUIT" 7 25)    ; 回路 - 白色
  (pdsg-create-layer "ANNOTATION" 3 18) ; 标注 - 绿色
  (pdsg-create-layer "FRAME" 5 35)      ; 图框 - 蓝色
  (pdsg-create-layer "CENTER" 1 9)      ; 中心线 - 红色点划线
  (princ "\n[INFO] 图层初始化完成")
)

;;; ------------------------------------------------------------
;;; 绘制母线
;;; ------------------------------------------------------------
(defun pdsg-draw-bus (x-start x-end y layer color lineweight / pt1 pt2)
  (pdsg-create-layer layer color lineweight)
  (setq pt1 (list x-start y 0.0))
  (setq pt2 (list x-end y 0.0))

  (command "_.LAYER" "_Set" layer "")
  (command "_.LINE" pt1 pt2 "")
  (command "_.LAYER" "_Set" "0" "")

  (princ (strcat "\n[INFO] 母线: (" (rtos x-start 2 1) "," (rtos y 2 1)
                 ") ~ (" (rtos x-end 2 1) "," (rtos y 2 1) ")"))
)

;;; ------------------------------------------------------------
;;; 绘制垂直引线
;;; ------------------------------------------------------------
(defun pdsg-draw-riser (x y-start y-end / pt1 pt2)
  (setq pt1 (list x y-start 0.0))
  (setq pt2 (list x y-end 0.0))
  (command "_.LINE" pt1 pt2 "")
)

;;; ------------------------------------------------------------
;;; 绘制图框
;;; ------------------------------------------------------------
(defun pdsg-draw-frame (paper-width paper-height title subtitle / 
                        tw th x y twidth theight)
  (pdsg-create-layer "FRAME" 5 35)

  (setq tw paper-width)
  (setq th paper-height)

  (command "_.LAYER" "_Set" "FRAME" "")

  ;; 外框
  (command "_.RECTANGLE" (list 0.0 0.0) (list tw th))

  ;; 标题栏区域（右下角 180x56mm）
  (setq twidth 180.0)
  (setq theight 56.0)
  (command "_.RECTANGLE" (list (- tw twidth) 0.0) (list tw theight))

  ;; 标题栏水平分隔线
  (command "_.LINE" (list (- tw twidth) (/ theight 2.0)) (list tw (/ theight 2.0)) "")

  ;; 标题栏垂直分隔线
  (command "_.LINE" (list (- tw 60) 0.0) (list (- tw 60) theight) "")

  ;; 标题文字
  (command "_.TEXT" "_Justify" "_MC"
           (list (- tw 120) (* theight 0.75)) 5.0 0.0 title)
  (command "_.TEXT" "_Justify" "_MC"
           (list (- tw 30) (* theight 0.75)) 3.0 0.0 subtitle)

  ;; 签名栏
  (command "_.TEXT" "_Justify" "_ML" (list (- tw 178) 4.0) 2.5 0.0 "设计:")
  (command "_.TEXT" "_Justify" "_ML" (list (- tw 178) 12.0) 2.5 0.0 "校核:")
  (command "_.TEXT" "_Justify" "_ML" (list (- tw 178) 20.0) 2.5 0.0 "审核:")
  (command "_.TEXT" "_Justify" "_ML" (list (- tw 178) 28.0) 2.5 0.0 "日期:")

  (command "_.LAYER" "_Set" "0" "")
  (princ "\n[INFO] 图框绘制完成")
)

;;; ------------------------------------------------------------
;;; 插入图块并设置属性
;;; ------------------------------------------------------------
(defun pdsg-insert-block (block-name position scale rotation attributes
                          / ent)
  (if (pdsg-block-exists block-name)
    (progn
      (command "_.INSERT" block-name position scale scale rotation)
      (setq ent (entlast))

      ;; 设置属性值
      (if (and ent attributes)
        (foreach attr attributes
          (pdsg-set-attribute ent (car attr) (cdr attr))
        )
      )
      ent
    )
    (progn
      (princ (strcat "\n[WARN] 图块不存在: " block-name "，使用默认图块"))
      (command "_.INSERT" "LOOP_DEFAULT" position 1.0 1.0 0.0)
      (entlast)
    )
  )
)

;;; ------------------------------------------------------------
;;; 设置图块属性值
;;; ------------------------------------------------------------
(defun pdsg-set-attribute (ent tag value / sub-ent ent-ent)
  (setq sub-ent (entnext ent))
  (while sub-ent
    (setq ent-ent (entget sub-ent))
    (if (and (= (cdr (assoc 0 ent-ent)) "ATTRIB")
             (= (cdr (assoc 2 ent-ent)) tag))
      (progn
        (setq ent-ent (subst (cons 1 value) (assoc 1 ent-ent) ent-ent))
        (entmod ent-ent)
        (entupd sub-ent)
      )
    )
    (setq sub-ent (entnext sub-ent))
  )
)

;;; ------------------------------------------------------------
;;; 设置文字样式
;;; ------------------------------------------------------------
(defun pdsg-setup-text-styles ()
  (princ "\n=== 初始化文字样式 ===")
  ;; 标准文字样式（如果不存在）
  (if (null (tblsearch "STYLE" "PDSG_TITLE"))
    (command "_.STYLE" "PDSG_TITLE" "Standard" "" "" "" "" "" "")
  )
  (if (null (tblsearch "STYLE" "PDSG_LABEL"))
    (command "_.STYLE" "PDSG_LABEL" "Standard" "" "" "" "" "" "")
  )
  (princ "\n[INFO] 文字样式初始化完成")
)

;;; ------------------------------------------------------------
;;; 初始化绘图环境
;;; ------------------------------------------------------------
(defun pdsg-init-drawing ()
  (princ "\n=== 初始化绘图环境 ===")
  (pdsg-setup-layers)
  (pdsg-setup-text-styles)

  ;; 设置单位
  (command "_.UNITS" 2 2 1 4 0 "N")

  ;; 设置标注样式
  (command "_.DIMSTYLE" "_Modify" "Standard"
           "_DIMTXT" 2.5
           "_DIMASZ" 2.0
           "_DIMEXE" 1.25
           "_DIMEXO" 0.625
           "_DIMDLE" 0.0
           "")

  (princ "\n[INFO] 绘图环境初始化完成")
)

(princ "\n[PDSG-LISP 绘图工具模块已加载]")