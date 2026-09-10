"""esquema inicial de la plataforma

Creates the full domain: tenancy, catalogue, CRM, commercial pipeline,
policies, renewals, communications and the intelligence layer.

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 2026-09-10T02:21:19.624127+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_esquema_inicial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    # gen_random_uuid() lives in pgcrypto on Postgres < 13 and in core after;
    # requesting the extension keeps the migration portable either way.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Enum types are created once, up front. Declaring them inline on each
    # column would emit CREATE TYPE several times for the shared ones
    # (`canal`, `tipo_cliente`, `nivel_riesgo`, `etapa_oportunidad`) and fail.
    canal_enum = postgresql.ENUM('web', 'whatsapp', 'telefono', 'presencial', 'referido', 'manual', name='canal')
    canal_enum.create(bind, checkfirst=True)
    direccion_comunicacion_enum = postgresql.ENUM('entrante', 'saliente', name='direccion_comunicacion')
    direccion_comunicacion_enum.create(bind, checkfirst=True)
    estado_cotizacion_enum = postgresql.ENUM('borrador', 'enviada', 'aceptada', 'rechazada', 'vencida', name='estado_cotizacion')
    estado_cotizacion_enum.create(bind, checkfirst=True)
    estado_poliza_enum = postgresql.ENUM('vigente', 'proxima_a_vencer', 'vencida', 'renovada', 'cancelada', name='estado_poliza')
    estado_poliza_enum.create(bind, checkfirst=True)
    estado_renovacion_enum = postgresql.ENUM('pendiente', 'en_gestion', 'completada', 'omitida', name='estado_renovacion')
    estado_renovacion_enum.create(bind, checkfirst=True)
    estado_solicitud_enum = postgresql.ENUM('nueva', 'asignada', 'en_proceso', 'convertida', 'descartada', name='estado_solicitud')
    estado_solicitud_enum.create(bind, checkfirst=True)
    etapa_oportunidad_enum = postgresql.ENUM('nuevo', 'contactado', 'cotizando', 'propuesta_enviada', 'en_negociacion', 'ganado', 'perdido', name='etapa_oportunidad')
    etapa_oportunidad_enum.create(bind, checkfirst=True)
    motivo_perdida_enum = postgresql.ENUM('precio', 'competencia', 'sin_respuesta', 'no_asegurable', 'desiste', 'otro', name='motivo_perdida')
    motivo_perdida_enum.create(bind, checkfirst=True)
    nivel_riesgo_enum = postgresql.ENUM('bajo', 'medio', 'alto', name='nivel_riesgo')
    nivel_riesgo_enum.create(bind, checkfirst=True)
    rol_usuario_enum = postgresql.ENUM('admin', 'gerente', 'asesor', name='rol_usuario')
    rol_usuario_enum.create(bind, checkfirst=True)
    tipo_cliente_enum = postgresql.ENUM('persona', 'empresa', name='tipo_cliente')
    tipo_cliente_enum.create(bind, checkfirst=True)
    tipo_documento_enum = postgresql.ENUM('cc', 'ce', 'nit', 'pasaporte', 'ti', name='tipo_documento')
    tipo_documento_enum.create(bind, checkfirst=True)

    op.create_table('tenants',
    sa.Column('slug', sa.String(length=63), nullable=False),
    sa.Column('nombre', sa.String(length=160), nullable=False),
    sa.Column('nit', sa.String(length=32), nullable=True),
    sa.Column('ciudad', sa.String(length=80), nullable=True),
    sa.Column('telefono', sa.String(length=32), nullable=True),
    sa.Column('email', sa.String(length=160), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('configuracion', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tenants')),
    sa.UniqueConstraint('slug', name=op.f('uq_tenants_slug'))
    )
    op.create_table('aseguradoras',
    sa.Column('nombre', sa.String(length=160), nullable=False),
    sa.Column('nit', sa.String(length=32), nullable=True),
    sa.Column('contacto', sa.String(length=160), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_aseguradoras_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_aseguradoras')),
    sa.UniqueConstraint('tenant_id', 'nombre', name='aseguradora_nombre_tenant')
    )
    op.create_table('consecutivos',
    sa.Column('entidad', sa.String(length=32), nullable=False),
    sa.Column('prefijo', sa.String(length=8), nullable=False),
    sa.Column('valor', sa.BigInteger(), nullable=False),
    sa.Column('ancho', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_consecutivos_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consecutivos')),
    sa.UniqueConstraint('tenant_id', 'entidad', name='consecutivo_entidad_tenant')
    )
    op.create_table('ramos',
    sa.Column('codigo', sa.String(length=48), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.String(length=500), nullable=True),
    sa.Column('dirigido_a', postgresql.ENUM(name='tipo_cliente', create_type=False), nullable=True),
    sa.Column('formulario', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_ramos_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ramos')),
    sa.UniqueConstraint('tenant_id', 'codigo', name='ramo_codigo_tenant')
    )
    op.create_table('usuarios',
    sa.Column('nombre', sa.String(length=160), nullable=False),
    sa.Column('email', sa.String(length=160), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('rol', postgresql.ENUM(name='rol_usuario', create_type=False), nullable=False),
    sa.Column('telefono', sa.String(length=32), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_usuarios_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuarios')),
    sa.UniqueConstraint('tenant_id', 'email', name='usuario_email_tenant')
    )
    op.create_table('clientes',
    sa.Column('tipo', postgresql.ENUM(name='tipo_cliente', create_type=False), nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('tipo_documento', postgresql.ENUM(name='tipo_documento', create_type=False), nullable=True),
    sa.Column('documento', sa.String(length=40), nullable=True),
    sa.Column('telefono', sa.String(length=32), nullable=True),
    sa.Column('email', sa.String(length=160), nullable=True),
    sa.Column('ciudad', sa.String(length=80), nullable=True),
    sa.Column('direccion', sa.String(length=240), nullable=True),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
    sa.Column('origen', postgresql.ENUM(name='canal', create_type=False), nullable=False),
    sa.Column('fecha_registro', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
    sa.Column('asesor_id', sa.UUID(), nullable=True),
    sa.Column('notas', sa.String(length=2000), nullable=True),
    sa.Column('perfil', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['asesor_id'], ['usuarios.id'], name=op.f('fk_clientes_asesor_id_usuarios'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_clientes_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_clientes')),
    sa.UniqueConstraint('tenant_id', 'documento', name='cliente_documento_tenant')
    )
    op.create_table('comunicaciones',
    sa.Column('cliente_id', sa.UUID(), nullable=False),
    sa.Column('canal', postgresql.ENUM(name='canal', create_type=False), nullable=False),
    sa.Column('direccion', postgresql.ENUM(name='direccion_comunicacion', create_type=False), nullable=False),
    sa.Column('contenido', sa.Text(), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=True),
    sa.Column('automatico', sa.Boolean(), nullable=False),
    sa.Column('external_id', sa.String(length=160), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_comunicaciones_cliente_id_clientes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_comunicaciones_tenant_id_tenants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_comunicaciones_usuario_id_usuarios'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_comunicaciones')),
    sa.UniqueConstraint('tenant_id', 'external_id', name='comunicacion_external_tenant')
    )
    op.create_table('recomendaciones_cross_sell',
    sa.Column('cliente_id', sa.UUID(), nullable=False),
    sa.Column('ramo_id', sa.UUID(), nullable=False),
    sa.Column('puntaje', sa.Float(), nullable=False),
    sa.Column('razon', sa.Text(), nullable=True),
    sa.Column('aceptada', sa.Boolean(), nullable=True),
    sa.Column('revisada_en', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('modelo', sa.String(length=64), nullable=False),
    sa.Column('modelo_version', sa.String(length=32), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('calculado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint('puntaje >= 0 AND puntaje <= 1', name=op.f('ck_recomendaciones_cross_sell_puntaje_normalizado')),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_recomendaciones_cross_sell_cliente_id_clientes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['ramo_id'], ['ramos.id'], name=op.f('fk_recomendaciones_cross_sell_ramo_id_ramos'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_recomendaciones_cross_sell_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recomendaciones_cross_sell')),
    sa.UniqueConstraint('cliente_id', 'ramo_id', 'modelo_version', name='recomendacion_cliente_ramo_version')
    )
    op.create_table('solicitudes',
    sa.Column('codigo', sa.String(length=24), nullable=False),
    sa.Column('cliente_id', sa.UUID(), nullable=False),
    sa.Column('ramo_id', sa.UUID(), nullable=False),
    sa.Column('canal', postgresql.ENUM(name='canal', create_type=False), nullable=False),
    sa.Column('estado', postgresql.ENUM(name='estado_solicitud', create_type=False), nullable=False),
    sa.Column('respuestas', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('formulario_version', sa.Integer(), nullable=False),
    sa.Column('asesor_id', sa.UUID(), nullable=True),
    sa.Column('asignada_en', sa.DateTime(), nullable=True),
    sa.Column('utm', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['asesor_id'], ['usuarios.id'], name=op.f('fk_solicitudes_asesor_id_usuarios'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_solicitudes_cliente_id_clientes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['ramo_id'], ['ramos.id'], name=op.f('fk_solicitudes_ramo_id_ramos'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_solicitudes_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_solicitudes')),
    sa.UniqueConstraint('tenant_id', 'codigo', name='solicitud_codigo_tenant')
    )
    op.create_table('analisis_mensajes',
    sa.Column('comunicacion_id', sa.UUID(), nullable=False),
    sa.Column('intencion', sa.String(length=48), nullable=False),
    sa.Column('confianza', sa.Float(), nullable=False),
    sa.Column('ramo_detectado_id', sa.UUID(), nullable=True),
    sa.Column('entidades', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('sentimiento', sa.Float(), nullable=True),
    sa.Column('requiere_humano', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('modelo', sa.String(length=64), nullable=False),
    sa.Column('modelo_version', sa.String(length=32), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('calculado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint('confianza >= 0 AND confianza <= 1', name=op.f('ck_analisis_mensajes_confianza_normalizada')),
    sa.ForeignKeyConstraint(['comunicacion_id'], ['comunicaciones.id'], name=op.f('fk_analisis_mensajes_comunicacion_id_comunicaciones'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['ramo_detectado_id'], ['ramos.id'], name=op.f('fk_analisis_mensajes_ramo_detectado_id_ramos'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_analisis_mensajes_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_analisis_mensajes'))
    )
    op.create_table('oportunidades',
    sa.Column('cliente_id', sa.UUID(), nullable=False),
    sa.Column('ramo_id', sa.UUID(), nullable=False),
    sa.Column('solicitud_id', sa.UUID(), nullable=True),
    sa.Column('asesor_id', sa.UUID(), nullable=True),
    sa.Column('etapa', postgresql.ENUM(name='etapa_oportunidad', create_type=False), nullable=False),
    sa.Column('valor_estimado', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('fecha_cierre_estimada', sa.Date(), nullable=True),
    sa.Column('cerrada_en', sa.DateTime(), nullable=True),
    sa.Column('motivo_perdida', postgresql.ENUM(name='motivo_perdida', create_type=False), nullable=True),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['asesor_id'], ['usuarios.id'], name=op.f('fk_oportunidades_asesor_id_usuarios'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_oportunidades_cliente_id_clientes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['ramo_id'], ['ramos.id'], name=op.f('fk_oportunidades_ramo_id_ramos'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes.id'], name=op.f('fk_oportunidades_solicitud_id_solicitudes'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_oportunidades_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_oportunidades')),
    sa.UniqueConstraint('solicitud_id', name=op.f('uq_oportunidades_solicitud_id'))
    )
    op.create_table('cotizaciones',
    sa.Column('codigo', sa.String(length=24), nullable=False),
    sa.Column('oportunidad_id', sa.UUID(), nullable=False),
    sa.Column('aseguradora_id', sa.UUID(), nullable=False),
    sa.Column('estado', postgresql.ENUM(name='estado_cotizacion', create_type=False), nullable=False),
    sa.Column('prima', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('deducible', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('valor_asegurado', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('vigencia_desde', sa.Date(), nullable=True),
    sa.Column('vigencia_hasta', sa.Date(), nullable=True),
    sa.Column('coberturas', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('enviada_en', sa.DateTime(), nullable=True),
    sa.Column('documento_url', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['aseguradora_id'], ['aseguradoras.id'], name=op.f('fk_cotizaciones_aseguradora_id_aseguradoras'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['oportunidad_id'], ['oportunidades.id'], name=op.f('fk_cotizaciones_oportunidad_id_oportunidades'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_cotizaciones_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cotizaciones')),
    sa.UniqueConstraint('tenant_id', 'codigo', name='cotizacion_codigo_tenant')
    )
    op.create_table('oportunidad_eventos',
    sa.Column('oportunidad_id', sa.UUID(), nullable=False),
    sa.Column('etapa_anterior', postgresql.ENUM(name='etapa_oportunidad', create_type=False), nullable=True),
    sa.Column('etapa_nueva', postgresql.ENUM(name='etapa_oportunidad', create_type=False), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=True),
    sa.Column('automatico', sa.Boolean(), nullable=False),
    sa.Column('nota', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['oportunidad_id'], ['oportunidades.id'], name=op.f('fk_oportunidad_eventos_oportunidad_id_oportunidades'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_oportunidad_eventos_tenant_id_tenants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_oportunidad_eventos_usuario_id_usuarios'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_oportunidad_eventos'))
    )
    op.create_table('polizas',
    sa.Column('numero', sa.String(length=64), nullable=False),
    sa.Column('cliente_id', sa.UUID(), nullable=False),
    sa.Column('ramo_id', sa.UUID(), nullable=False),
    sa.Column('aseguradora_id', sa.UUID(), nullable=False),
    sa.Column('asesor_id', sa.UUID(), nullable=True),
    sa.Column('oportunidad_id', sa.UUID(), nullable=True),
    sa.Column('fecha_inicio', sa.Date(), nullable=False),
    sa.Column('fecha_vencimiento', sa.Date(), nullable=False),
    sa.Column('prima', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('valor_asegurado', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('estado', postgresql.ENUM(name='estado_poliza', create_type=False), nullable=False),
    sa.Column('poliza_anterior_id', sa.UUID(), nullable=True),
    sa.Column('detalles', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('documento_url', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('fecha_vencimiento > fecha_inicio', name=op.f('ck_polizas_vigencia_coherente')),
    sa.ForeignKeyConstraint(['aseguradora_id'], ['aseguradoras.id'], name=op.f('fk_polizas_aseguradora_id_aseguradoras'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['asesor_id'], ['usuarios.id'], name=op.f('fk_polizas_asesor_id_usuarios'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name=op.f('fk_polizas_cliente_id_clientes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['oportunidad_id'], ['oportunidades.id'], name=op.f('fk_polizas_oportunidad_id_oportunidades'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['poliza_anterior_id'], ['polizas.id'], name=op.f('fk_polizas_poliza_anterior_id_polizas'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['ramo_id'], ['ramos.id'], name=op.f('fk_polizas_ramo_id_ramos'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_polizas_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_polizas')),
    sa.UniqueConstraint('tenant_id', 'aseguradora_id', 'numero', name='poliza_numero_aseguradora')
    )
    op.create_table('puntajes_lead',
    sa.Column('oportunidad_id', sa.UUID(), nullable=False),
    sa.Column('puntaje', sa.Float(), nullable=False),
    sa.Column('nivel', postgresql.ENUM(name='nivel_riesgo', create_type=False), nullable=False),
    sa.Column('explicacion', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('modelo', sa.String(length=64), nullable=False),
    sa.Column('modelo_version', sa.String(length=32), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('calculado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint('puntaje >= 0 AND puntaje <= 1', name=op.f('ck_puntajes_lead_puntaje_normalizado')),
    sa.ForeignKeyConstraint(['oportunidad_id'], ['oportunidades.id'], name=op.f('fk_puntajes_lead_oportunidad_id_oportunidades'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_puntajes_lead_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_puntajes_lead'))
    )
    op.create_table('renovaciones',
    sa.Column('poliza_id', sa.UUID(), nullable=False),
    sa.Column('umbral_dias', sa.Integer(), nullable=False),
    sa.Column('fecha_objetivo', sa.Date(), nullable=False),
    sa.Column('estado', postgresql.ENUM(name='estado_renovacion', create_type=False), nullable=False),
    sa.Column('asesor_id', sa.UUID(), nullable=True),
    sa.Column('completada_en', sa.DateTime(), nullable=True),
    sa.Column('notificado_en', sa.DateTime(), nullable=True),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('umbral_dias >= 0', name=op.f('ck_renovaciones_umbral_no_negativo')),
    sa.ForeignKeyConstraint(['asesor_id'], ['usuarios.id'], name=op.f('fk_renovaciones_asesor_id_usuarios'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['poliza_id'], ['polizas.id'], name=op.f('fk_renovaciones_poliza_id_polizas'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_renovaciones_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_renovaciones')),
    sa.UniqueConstraint('poliza_id', 'umbral_dias', name='renovacion_umbral_poliza')
    )
    op.create_table('riesgos_renovacion',
    sa.Column('poliza_id', sa.UUID(), nullable=False),
    sa.Column('probabilidad_fuga', sa.Float(), nullable=False),
    sa.Column('nivel', postgresql.ENUM(name='nivel_riesgo', create_type=False), nullable=False),
    sa.Column('explicacion', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('modelo', sa.String(length=64), nullable=False),
    sa.Column('modelo_version', sa.String(length=32), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('calculado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint('probabilidad_fuga >= 0 AND probabilidad_fuga <= 1', name=op.f('ck_riesgos_renovacion_probabilidad_normalizada')),
    sa.ForeignKeyConstraint(['poliza_id'], ['polizas.id'], name=op.f('fk_riesgos_renovacion_poliza_id_polizas'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_riesgos_renovacion_tenant_id_tenants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_riesgos_renovacion'))
    )
    # ### end Alembic commands ###

    op.create_index('ix_aseguradoras_tenant_id', 'aseguradoras', ['tenant_id'])
    op.create_index('ix_consecutivos_tenant_id', 'consecutivos', ['tenant_id'])
    op.create_index('ix_ramos_tenant_id', 'ramos', ['tenant_id'])
    op.create_index('ix_usuarios_tenant_id', 'usuarios', ['tenant_id'])
    op.create_index('ix_clientes_asesor_id', 'clientes', ['asesor_id'])
    op.create_index('ix_clientes_tenant_email', 'clientes', ['tenant_id', 'email'])
    op.create_index('ix_clientes_tenant_id', 'clientes', ['tenant_id'])
    op.create_index('ix_clientes_tenant_telefono', 'clientes', ['tenant_id', 'telefono'])
    op.create_index('ix_comunicaciones_cliente_created', 'comunicaciones', ['cliente_id', 'created_at'])
    op.create_index('ix_comunicaciones_cliente_id', 'comunicaciones', ['cliente_id'])
    op.create_index('ix_comunicaciones_tenant_id', 'comunicaciones', ['tenant_id'])
    op.create_index('ix_recomendaciones_cross_sell_cliente_id', 'recomendaciones_cross_sell', ['cliente_id'])
    op.create_index('ix_recomendaciones_cross_sell_tenant_id', 'recomendaciones_cross_sell', ['tenant_id'])
    op.create_index('ix_recomendaciones_tenant_puntaje', 'recomendaciones_cross_sell', ['tenant_id', 'puntaje'])
    op.create_index('ix_solicitudes_asesor_id', 'solicitudes', ['asesor_id'])
    op.create_index('ix_solicitudes_cliente_id', 'solicitudes', ['cliente_id'])
    op.create_index('ix_solicitudes_ramo_id', 'solicitudes', ['ramo_id'])
    op.create_index('ix_solicitudes_tenant_estado', 'solicitudes', ['tenant_id', 'estado'])
    op.create_index('ix_solicitudes_tenant_id', 'solicitudes', ['tenant_id'])
    op.create_index('ix_analisis_mensajes_comunicacion_id', 'analisis_mensajes', ['comunicacion_id'], unique=True)
    op.create_index('ix_analisis_mensajes_tenant_id', 'analisis_mensajes', ['tenant_id'])
    op.create_index('ix_oportunidades_cliente_id', 'oportunidades', ['cliente_id'])
    op.create_index('ix_oportunidades_ramo_id', 'oportunidades', ['ramo_id'])
    op.create_index('ix_oportunidades_tenant_asesor', 'oportunidades', ['tenant_id', 'asesor_id'])
    op.create_index('ix_oportunidades_tenant_etapa', 'oportunidades', ['tenant_id', 'etapa'])
    op.create_index('ix_oportunidades_tenant_id', 'oportunidades', ['tenant_id'])
    op.create_index('ix_cotizaciones_oportunidad_id', 'cotizaciones', ['oportunidad_id'])
    op.create_index('ix_cotizaciones_tenant_id', 'cotizaciones', ['tenant_id'])
    op.create_index('ix_oportunidad_eventos_oportunidad_id', 'oportunidad_eventos', ['oportunidad_id'])
    op.create_index('ix_oportunidad_eventos_tenant_created', 'oportunidad_eventos', ['tenant_id', 'created_at'])
    op.create_index('ix_oportunidad_eventos_tenant_id', 'oportunidad_eventos', ['tenant_id'])
    op.create_index('ix_polizas_asesor_id', 'polizas', ['asesor_id'])
    op.create_index('ix_polizas_cliente_id', 'polizas', ['cliente_id'])
    op.create_index('ix_polizas_ramo_id', 'polizas', ['ramo_id'])
    op.create_index('ix_polizas_tenant_estado', 'polizas', ['tenant_id', 'estado'])
    op.create_index('ix_polizas_tenant_id', 'polizas', ['tenant_id'])
    op.create_index('ix_polizas_tenant_vencimiento', 'polizas', ['tenant_id', 'fecha_vencimiento'])
    op.create_index('ix_puntajes_lead_oportunidad_id', 'puntajes_lead', ['oportunidad_id'])
    op.create_index('ix_puntajes_lead_tenant_calculado', 'puntajes_lead', ['tenant_id', 'calculado_en'])
    op.create_index('ix_puntajes_lead_tenant_id', 'puntajes_lead', ['tenant_id'])
    op.create_index('ix_renovaciones_asesor_id', 'renovaciones', ['asesor_id'])
    op.create_index('ix_renovaciones_poliza_id', 'renovaciones', ['poliza_id'])
    op.create_index('ix_renovaciones_tenant_estado', 'renovaciones', ['tenant_id', 'estado'])
    op.create_index('ix_renovaciones_tenant_id', 'renovaciones', ['tenant_id'])
    op.create_index('ix_renovaciones_tenant_objetivo', 'renovaciones', ['tenant_id', 'fecha_objetivo'])
    op.create_index('ix_riesgos_renovacion_poliza_id', 'riesgos_renovacion', ['poliza_id'])
    op.create_index('ix_riesgos_renovacion_tenant_id', 'riesgos_renovacion', ['tenant_id'])
    op.create_index('ix_riesgos_renovacion_tenant_nivel', 'riesgos_renovacion', ['tenant_id', 'nivel'])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index('ix_aseguradoras_tenant_id', table_name='aseguradoras')
    op.drop_index('ix_consecutivos_tenant_id', table_name='consecutivos')
    op.drop_index('ix_ramos_tenant_id', table_name='ramos')
    op.drop_index('ix_usuarios_tenant_id', table_name='usuarios')
    op.drop_index('ix_clientes_asesor_id', table_name='clientes')
    op.drop_index('ix_clientes_tenant_email', table_name='clientes')
    op.drop_index('ix_clientes_tenant_id', table_name='clientes')
    op.drop_index('ix_clientes_tenant_telefono', table_name='clientes')
    op.drop_index('ix_comunicaciones_cliente_created', table_name='comunicaciones')
    op.drop_index('ix_comunicaciones_cliente_id', table_name='comunicaciones')
    op.drop_index('ix_comunicaciones_tenant_id', table_name='comunicaciones')
    op.drop_index('ix_recomendaciones_cross_sell_cliente_id', table_name='recomendaciones_cross_sell')
    op.drop_index('ix_recomendaciones_cross_sell_tenant_id', table_name='recomendaciones_cross_sell')
    op.drop_index('ix_recomendaciones_tenant_puntaje', table_name='recomendaciones_cross_sell')
    op.drop_index('ix_solicitudes_asesor_id', table_name='solicitudes')
    op.drop_index('ix_solicitudes_cliente_id', table_name='solicitudes')
    op.drop_index('ix_solicitudes_ramo_id', table_name='solicitudes')
    op.drop_index('ix_solicitudes_tenant_estado', table_name='solicitudes')
    op.drop_index('ix_solicitudes_tenant_id', table_name='solicitudes')
    op.drop_index('ix_analisis_mensajes_comunicacion_id', table_name='analisis_mensajes')
    op.drop_index('ix_analisis_mensajes_tenant_id', table_name='analisis_mensajes')
    op.drop_index('ix_oportunidades_cliente_id', table_name='oportunidades')
    op.drop_index('ix_oportunidades_ramo_id', table_name='oportunidades')
    op.drop_index('ix_oportunidades_tenant_asesor', table_name='oportunidades')
    op.drop_index('ix_oportunidades_tenant_etapa', table_name='oportunidades')
    op.drop_index('ix_oportunidades_tenant_id', table_name='oportunidades')
    op.drop_index('ix_cotizaciones_oportunidad_id', table_name='cotizaciones')
    op.drop_index('ix_cotizaciones_tenant_id', table_name='cotizaciones')
    op.drop_index('ix_oportunidad_eventos_oportunidad_id', table_name='oportunidad_eventos')
    op.drop_index('ix_oportunidad_eventos_tenant_created', table_name='oportunidad_eventos')
    op.drop_index('ix_oportunidad_eventos_tenant_id', table_name='oportunidad_eventos')
    op.drop_index('ix_polizas_asesor_id', table_name='polizas')
    op.drop_index('ix_polizas_cliente_id', table_name='polizas')
    op.drop_index('ix_polizas_ramo_id', table_name='polizas')
    op.drop_index('ix_polizas_tenant_estado', table_name='polizas')
    op.drop_index('ix_polizas_tenant_id', table_name='polizas')
    op.drop_index('ix_polizas_tenant_vencimiento', table_name='polizas')
    op.drop_index('ix_puntajes_lead_oportunidad_id', table_name='puntajes_lead')
    op.drop_index('ix_puntajes_lead_tenant_calculado', table_name='puntajes_lead')
    op.drop_index('ix_puntajes_lead_tenant_id', table_name='puntajes_lead')
    op.drop_index('ix_renovaciones_asesor_id', table_name='renovaciones')
    op.drop_index('ix_renovaciones_poliza_id', table_name='renovaciones')
    op.drop_index('ix_renovaciones_tenant_estado', table_name='renovaciones')
    op.drop_index('ix_renovaciones_tenant_id', table_name='renovaciones')
    op.drop_index('ix_renovaciones_tenant_objetivo', table_name='renovaciones')
    op.drop_index('ix_riesgos_renovacion_poliza_id', table_name='riesgos_renovacion')
    op.drop_index('ix_riesgos_renovacion_tenant_id', table_name='riesgos_renovacion')
    op.drop_index('ix_riesgos_renovacion_tenant_nivel', table_name='riesgos_renovacion')

    op.drop_table('riesgos_renovacion')
    op.drop_table('renovaciones')
    op.drop_table('puntajes_lead')
    op.drop_table('polizas')
    op.drop_table('oportunidad_eventos')
    op.drop_table('cotizaciones')
    op.drop_table('oportunidades')
    op.drop_table('analisis_mensajes')
    op.drop_table('solicitudes')
    op.drop_table('recomendaciones_cross_sell')
    op.drop_table('comunicaciones')
    op.drop_table('clientes')
    op.drop_table('usuarios')
    op.drop_table('ramos')
    op.drop_table('consecutivos')
    op.drop_table('aseguradoras')
    op.drop_table('tenants')

    postgresql.ENUM(name='canal').drop(bind, checkfirst=True)
    postgresql.ENUM(name='direccion_comunicacion').drop(bind, checkfirst=True)
    postgresql.ENUM(name='estado_cotizacion').drop(bind, checkfirst=True)
    postgresql.ENUM(name='estado_poliza').drop(bind, checkfirst=True)
    postgresql.ENUM(name='estado_renovacion').drop(bind, checkfirst=True)
    postgresql.ENUM(name='estado_solicitud').drop(bind, checkfirst=True)
    postgresql.ENUM(name='etapa_oportunidad').drop(bind, checkfirst=True)
    postgresql.ENUM(name='motivo_perdida').drop(bind, checkfirst=True)
    postgresql.ENUM(name='nivel_riesgo').drop(bind, checkfirst=True)
    postgresql.ENUM(name='rol_usuario').drop(bind, checkfirst=True)
    postgresql.ENUM(name='tipo_cliente').drop(bind, checkfirst=True)
    postgresql.ENUM(name='tipo_documento').drop(bind, checkfirst=True)
