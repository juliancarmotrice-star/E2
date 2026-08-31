---
name: supabase-integration
description: >-
  Guidelines and procedures for interacting with Supabase, managing PostgreSQL database schemas,
  writing migrations, executing queries, and synchronizing project data with Supabase.
---

# Supabase Integration & Database Guidelines

This skill provides patterns and best practices for managing Supabase database operations for E2 SAS project.

## Project Details
- **Project Ref:** `wheclfavngzgmlhbojrd`
- **MCP Endpoint:** `https://mcp.supabase.com/mcp?project_ref=wheclfavngzgmlhbojrd&features=docs%2Caccount%2Cdatabase%2Cdebugging%2Cdevelopment%2Cfunctions%2Cbranching`

## Data Model & Tables
The project integrates 8 primary datasets into PostgreSQL:
1. `maestro_materiales` (SKU PK, description, category, unit, cost, vendor, lead time, min/max)
2. `ordenes_compra` (PO PK, dates, SKU FK, quantity, vendor, costs)
3. `movimientos_inventario` (date, SKU FK, movement type, quantity, document, warehouse, responsible)
4. `bom` (product FK, name, component SKU FK, quantity per unit)
5. `plan_produccion` (period, product, planned vs real quantities)
6. `inventario_inicial` (SKU FK, initial stock, date)
7. `conteo_fisico` (SKU FK, counted stock, date)
8. `inventario_bodega_jefe` (SKU FK, stock, notes)

## Connection Strategies
1. **MCP Server**: Registered in `.agents/mcp_config.json` for tool calling and remote introspection.
2. **Python Client / SQLAlchemy**: For ETL pipelines and data loading using `.env` credentials (`SUPABASE_URL`, `SUPABASE_KEY` or `DATABASE_URL`).
