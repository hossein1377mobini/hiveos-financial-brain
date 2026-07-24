# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\src\\hiveos\\dashboard\\templates', 'hiveos/dashboard/templates'), ('C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\src\\hiveos\\dashboard\\static', 'hiveos/dashboard/static'), ('C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\domains', 'domains'), ('C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\prototype', 'prototype')]
binaries = []
hiddenimports = ['hiveos', 'hiveos.cli.main', 'hiveos.cli.build', 'hiveos.desktop', 'hiveos.desktop.app', 'hiveos.dashboard', 'hiveos.dashboard.server', 'hiveos.dashboard.app', 'hiveos.dashboard.auth', 'hiveos.dashboard.config_service', 'hiveos.dashboard.routes', 'hiveos.dashboard.routes.config', 'hiveos.dashboard.routes.deps', 'hiveos.dashboard.routes.domain_packs', 'hiveos.dashboard.routes.history', 'hiveos.dashboard.routes.knowledge', 'hiveos.dashboard.routes.skills', 'hiveos.dashboard.routes.workflows', 'hiveos.playground', 'hiveos.playground.playground', 'hiveos.playground.runner', 'hiveos.playground.library', 'hiveos.brain', 'hiveos.brain.approval_gate', 'hiveos.brain.decision_tracer', 'hiveos.brain.event_stream', 'hiveos.learning', 'hiveos.learning.analytics', 'hiveos.storage', 'hiveos.storage.engine', 'hiveos.domain', 'hiveos.domain.manager', 'hiveos.domain.registry', 'hiveos.domain_pack', 'hiveos.domain_pack.manager', 'hiveos.domain_pack.models', 'hiveos.domain_pack.registry', 'hiveos.domain_pack.validator', 'hiveos.domain_pack.loader', 'hiveos.knowledge', 'hiveos.knowledge.service', 'hiveos.knowledge.indexing', 'hiveos.knowledge.search', 'hiveos.knowledge.ingestion', 'hiveos.audit', 'hiveos.audit.trail', 'hiveos.audit.models', 'hiveos.rbac', 'hiveos.update', 'hiveos.package', 'hiveos.registry', 'hiveos.mothership', 'hiveos.mothership.communication_bus', 'hiveos.mothership.task_router', 'hiveos.sync', 'hiveos.utils.config', 'hiveos.utils.validator', 'hiveos.utils.knowledge', 'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'websockets', 'websockets.legacy', 'websockets.legacy.client', 'pydantic', 'pydantic_core', 'fastapi', 'fastapi.responses', 'fastapi.staticfiles', 'fastapi.templating', 'click', 'click.core', 'click.types', 'rich', 'rich.console', 'rich.panel', 'rich.table', 'yaml']
tmp_ret = collect_all('hiveos')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\src\\hiveos\\desktop\\app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pythoncom', 'pywin32'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HiveOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Hossein Mobini\\Desktop\\hive-os\\build\\hiveos.ico'],
)
