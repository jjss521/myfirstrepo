# -*- coding: utf-8 -*-
"""FastAPI 后端入口（未来 Web 服务的基础）。"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))          # backend/app
sys.path.insert(0, os.path.dirname(_HERE))                   # backend

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.database import init_db, SessionLocal
from app.models import ProjectType, Section, Document, GenerationLog
from app.schemas import GenerateRequest, GenerateResponse, ProjectTypeOut, SectionOut, UploadResponse
from app.services.excel_parser import parse as parse_excel
from app.services.docx_generator import DocxGenerator
from app.config import UPLOAD_DIR

init_db()

app = FastAPI(title='市政工程设计文件电气自控生成器 API', version='1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/project-types', response_model=list[ProjectTypeOut])
def project_types():
    db = SessionLocal()
    rows = db.query(ProjectType).all()
    db.close()
    return [ProjectTypeOut(id=r.id, code=r.code, name=r.name,
                           design_stage=r.design_stage, description=r.description or '') for r in rows]


@app.get('/api/sections', response_model=list[SectionOut])
def sections():
    db = SessionLocal()
    rows = db.query(Section).all()
    db.close()
    return [SectionOut(id=r.id, project_type_id=r.project_type_id, category=r.category,
                       section_order=r.section_order, title=r.title,
                       depth_requirement=r.depth_requirement or '',
                       has_calculation=bool(r.has_calculation),
                       table_required=bool(r.table_required),
                       calc_from_excel=bool(r.calc_from_excel),
                       optional=bool(r.optional)) for r in rows]


@app.post('/api/generate', response_model=GenerateResponse)
def generate(req: GenerateRequest):
    if not os.path.exists(req.excel_path):
        return GenerateResponse(output_path='', project_name=req.project_name,
                                project_type=req.project_type, design_stage=req.design_stage,
                                template=req.template, summary={})
    ed = parse_excel(req.excel_path)
    params = {
        'project_name': req.project_name,
        'voltage_level': req.voltage_level,
        'load_level': req.load_level,
        'project_type': req.project_type,
        'design_stage': req.design_stage,
        'power_source': req.power_source,
        'standby_desc': req.standby_desc,
    }
    gen = DocxGenerator(template=req.template)
    out = gen.generate(req.project_type, req.design_stage, ed, params)
    # 记录生成日志
    db = SessionLocal()
    db.add(GenerationLog(project_name=req.project_name, project_type=req.project_type,
                         design_stage=req.design_stage, template=req.template,
                         excel_path=req.excel_path, output_path=out))
    db.commit()
    db.close()
    return GenerateResponse(output_path=out, project_name=req.project_name,
                            project_type=req.project_type, design_stage=req.design_stage,
                            template=req.template, summary=ed.get('summary', {}))


@app.post('/api/upload', response_model=UploadResponse)
def upload(file: UploadFile = File(...), doc_type: str = 'reference'):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, 'wb') as f:
        shutil_copy(file, f)
    db = SessionLocal()
    d = Document(filename=file.filename, original_name=file.filename,
                 doc_type=doc_type, project_type='', design_stage='')
    db.add(d)
    db.commit()
    db.refresh(d)
    db.close()
    return UploadResponse(id=d.id, filename=file.filename, original_name=file.filename, doc_type=doc_type)


def shutil_copy(file, f):
    import shutil
    shutil.copyfileobj(file.file, f)


@app.get('/api/download')
def download(path: str):
    if os.path.exists(path):
        return FileResponse(path, filename=os.path.basename(path))
    return {'error': 'not found'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
