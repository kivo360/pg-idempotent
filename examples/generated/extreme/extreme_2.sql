-- Generated Test Case: extreme_2
-- Complexity: extreme
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Migration 1: Polymorphic type system with circular dependencies and dynamic partitioning
-- This creates a self-referential hierarchy with JSON validation, dynamic SQL, and runtime type checking

BEGIN;

-- Create enum type that will be used in polymorphic relationships
CREATE TYPE entity_type AS ENUM (
    'user', 
    'organization', 
    'department', 
    'project'
);

-- Create polymorphic base table with JSON schema validation
CREATE TABLE entities (
    id BIGSERIAL PRIMARY KEY,
    type entity_type NOT NULL,
    parent_id BIGINT,
    attributes JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Circular reference to parent
    CONSTRAINT fk_parent FOREIGN KEY (parent_id, type) 
        REFERENCES entities(id, type) 
        DEFERRABLE INITIALLY DEFERRED,
    
    -- Dynamic type-specific validation
    CONSTRAINT valid_attributes CHECK (
        CASE type
            WHEN 'user' THEN attributes @> '{"email": "", "name": ""}'
            WHEN 'organization' THEN attributes ? 'legal_name'
            WHEN 'department' THEN attributes ?& ARRAY['name', 'cost_center']
            WHEN 'project' THEN attributes ? 'code'
            ELSE false
        END
    )
) PARTITION BY LIST (type);

-- Dynamic partition creation with PL/pgSQL
DO $$
DECLARE
    t entity_type;
BEGIN
    FOR t IN SELECT unnest(enum_range(NULL::entity_type)) LOOP
        EXECUTE format('
            CREATE TABLE entities_%s PARTITION OF entities 
            FOR VALUES IN (%L)
            PARTITION BY RANGE (created_at)
        ', t, t);
        
        -- Create monthly subpartitions for each type
        EXECUTE format('
            CREATE TABLE entities_%s_%s PARTITION OF entities_%s
            FOR VALUES FROM (%L) TO (%L)
        ', 
        t, 
        to_char(CURRENT_DATE, 'YYYY_MM'),
        t,
        date_trunc('month', CURRENT_DATE),
        date_trunc('month', CURRENT_DATE + INTERVAL '1 month'));
    END LOOP;
END;
$$;

-- Create polymorphic function that behaves differently per entity type
CREATE OR REPLACE FUNCTION get_display_name(entity_id BIGINT) 
RETURNS TEXT AS $$
DECLARE
    e_type entity_type;
    result TEXT;
BEGIN
    SELECT type INTO e_type FROM entities WHERE id = entity_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Entity % not found', entity_id;
    END IF;
    
    EXECUTE format('
        SELECT 
            CASE WHEN type = ''user'' THEN 
                attributes->>''name'' || '' ('' || attributes->>''email'' || '')''
            WHEN type = ''organization'' THEN 
                attributes->>''legal_name''
            ELSE 
                attributes->>''name''
            END
        FROM entities_%I WHERE id = %s',
        e_type, entity_id)
    INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create recursive materialized view that depends on the polymorphic function
CREATE MATERIALIZED VIEW entity_hierarchies AS
WITH RECURSIVE hierarchy AS (
    SELECT 
        id,
        parent_id,
        type,
        get_display_name(id) AS display_name,
        ARRAY[id] AS path,
        1 AS depth
    FROM entities
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT 
        e.id,
        e.parent_id,
        e.type,
        get_display_name(e.id) AS display_name,
        h.path || e.id,
        h.depth + 1
    FROM entities e
    JOIN hierarchy h ON e.parent_id = h.id
)
SELECT * FROM hierarchy;

-- This will fail if run twice due to:
-- 1. Duplicate partitions
-- 2. Duplicate enum type
-- 3. Duplicate polymorphic function
-- 4. Circular foreign key checks

COMMIT;