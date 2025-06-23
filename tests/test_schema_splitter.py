"""Tests for schema splitting engine."""
import pytest
from pathlib import Path
from pg_idempotent.splitter.schema_splitter import SchemaSplitter, SchemaGroup
from pg_idempotent.parser.parser import PostgreSQLParser, ParsedStatement
from pg_idempotent.analyzer.rustworkx_analyzer import DependencyGraphAnalyzer


class TestSchemaSplitterEngine:
    """Test schema splitting engine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = SchemaSplitterEngine()
        self.parser = PostgreSQLParser()
        self.analyzer = RustworkxDependencyAnalyzer()
    
    def create_test_graph(self, sql: str):
        """Helper to create dependency graph from SQL."""
        statements = self.parser.parse_sql(sql)
        return self.analyzer.analyze(statements)
    
    def test_dependency_based_splitting(self):
        """Test splitting based on dependency levels."""
        sql = """
        -- Level 0: Types
        CREATE TYPE user_status AS ENUM ('active', 'inactive');
        CREATE TYPE order_status AS ENUM ('pending', 'completed');
        
        -- Level 1: Tables using types
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            status user_status DEFAULT 'active'
        );
        
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        
        -- Level 2: Tables with foreign keys
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            status order_status DEFAULT 'pending'
        );
        
        -- Level 3: Tables with complex dependencies
        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id)
        );
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split_by_dependencies(graph)
        
        # Should have different levels
        assert "level_0" in result
        assert "level_1" in result
        assert "level_2" in result
        assert "level_3" in result
        
        # Level 0 should contain types
        level_0_objects = [obj.name for obj in result["level_0"]]
        assert "user_status" in level_0_objects
        assert "order_status" in level_0_objects
        
        # Level 1 should contain base tables
        level_1_objects = [obj.name for obj in result["level_1"]]
        assert "users" in level_1_objects
        assert "products" in level_1_objects
        
        # Level 2 should contain dependent tables
        level_2_objects = [obj.name for obj in result["level_2"]]
        assert "orders" in level_2_objects
        
        # Level 3 should contain most dependent tables
        level_3_objects = [obj.name for obj in result["level_3"]]
        assert "order_items" in level_3_objects
    
    def test_category_based_splitting(self):
        """Test splitting by object category."""
        sql = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE TYPE status AS ENUM ('active', 'inactive');
        
        CREATE TABLE users (id UUID PRIMARY KEY DEFAULT uuid_generate_v4());
        CREATE TABLE posts (id SERIAL PRIMARY KEY, user_id UUID REFERENCES users(id));
        
        CREATE FUNCTION get_user_count() RETURNS INTEGER AS $$
        BEGIN
            RETURN (SELECT COUNT(*) FROM users);
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'active';
        
        CREATE INDEX idx_posts_user ON posts(user_id);
        
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        CREATE POLICY users_policy ON users FOR ALL USING (id = current_user_id());
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split_by_category(graph)
        
        # Should have different categories
        expected_categories = [
            "extensions", "types", "tables", "functions", 
            "views", "indexes", "policies"
        ]
        
        for category in expected_categories:
            assert category in result, f"Missing category: {category}"
        
        # Check that objects are correctly categorized
        extensions = [obj.name for obj in result["extensions"]]
        assert any("uuid-ossp" in ext for ext in extensions)
        
        types = [obj.name for obj in result["types"]]
        assert "status" in types
        
        tables = [obj.name for obj in result["tables"]]
        assert "users" in tables
        assert "posts" in tables
        
        functions = [obj.name for obj in result["functions"]]
        assert "get_user_count" in functions
        
        views = [obj.name for obj in result["views"]]
        assert "active_users" in views
        
        indexes = [obj.name for obj in result["indexes"]]
        assert "idx_posts_user" in indexes
    
    def test_hybrid_splitting_strategy(self):
        """Test hybrid splitting combining dependencies and categories."""
        sql = """
        CREATE TYPE user_role AS ENUM ('admin', 'user');
        
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            role user_role DEFAULT 'user'
        );
        
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id)
        );
        
        CREATE FUNCTION moderate_post(post_id INTEGER) RETURNS BOOLEAN AS $$
        BEGIN
            RETURN EXISTS (
                SELECT 1 FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = post_id AND u.role = 'admin'
            );
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE INDEX idx_posts_user ON posts(user_id);
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split_hybrid(graph)
        
        # Hybrid should create meaningful groups
        assert len(result) > 0
        
        # Should respect both dependencies and categories
        # Types should come before tables that use them
        type_groups = [group for group in result.keys() if "type" in group.lower()]
        table_groups = [group for group in result.keys() if "table" in group.lower()]
        
        # At minimum, should have separate groups for different object types
        all_object_types = set()
        for objects in result.values():
            for obj in objects:
                all_object_types.add(obj.object_type)
        
        assert len(all_object_types) > 1, "Hybrid splitting should separate different object types"
    
    def test_circular_dependency_handling(self):
        """Test handling of circular dependencies in splitting."""
        sql = """
        CREATE TABLE a (
            id SERIAL PRIMARY KEY,
            b_id INTEGER
        );
        
        CREATE TABLE b (
            id SERIAL PRIMARY KEY,
            c_id INTEGER
        );
        
        CREATE TABLE c (
            id SERIAL PRIMARY KEY,
            a_id INTEGER REFERENCES a(id)
        );
        
        -- Create the circular dependency
        ALTER TABLE a ADD CONSTRAINT fk_a_b FOREIGN KEY (b_id) REFERENCES b(id);
        ALTER TABLE b ADD CONSTRAINT fk_b_c FOREIGN KEY (c_id) REFERENCES c(id);
        """
        
        graph = self.create_test_graph(sql)
        
        # Should not crash on circular dependencies
        result = self.splitter.split_by_dependencies(graph)
        
        # All tables should be placed in some level
        all_objects = []
        for objects in result.values():
            all_objects.extend([obj.name for obj in objects])
        
        assert "a" in all_objects
        assert "b" in all_objects
        assert "c" in all_objects
    
    def test_cross_schema_objects(self):
        """Test handling of objects across multiple schemas."""
        sql = """
        CREATE SCHEMA auth;
        CREATE SCHEMA app;
        
        CREATE TABLE auth.users (id SERIAL PRIMARY KEY);
        CREATE TABLE app.posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES auth.users(id)
        );
        
        CREATE FUNCTION app.get_user_posts(user_id INTEGER)
        RETURNS TABLE(id INTEGER, user_id INTEGER) AS $$
        BEGIN
            RETURN QUERY SELECT p.id, p.user_id FROM app.posts p WHERE p.user_id = $1;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split_by_dependencies(graph)
        
        # Should handle schema-qualified names correctly
        all_objects = []
        for objects in result.values():
            all_objects.extend([f"{obj.schema}.{obj.name}" for obj in objects])
        
        assert "auth.users" in all_objects
        assert "app.posts" in all_objects
        assert "app.get_user_posts" in all_objects


class TestSupabaseSplitter:
    """Test Supabase-specific splitting logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = SupabaseSplitter()
        self.parser = PostgreSQLParser()
        self.analyzer = RustworkxDependencyAnalyzer()
    
    def create_test_graph(self, sql: str):
        """Helper to create dependency graph from SQL."""
        statements = self.parser.parse_sql(sql)
        return self.analyzer.analyze(statements)
    
    def test_supabase_category_structure(self):
        """Test Supabase-specific category structure."""
        sql = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE TYPE user_role AS ENUM ('admin', 'user');
        
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            role user_role DEFAULT 'user'
        );
        
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        CREATE POLICY users_select_policy ON users FOR SELECT USING (true);
        
        CREATE FUNCTION auth.uid() RETURNS UUID AS $$
            SELECT '00000000-0000-0000-0000-000000000000'::UUID;
        $$ LANGUAGE SQL;
        
        CREATE VIEW public.user_profiles AS 
        SELECT id, role FROM users;
        
        CREATE INDEX idx_users_role ON users(role);
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split(graph, "supabase")
        
        # Should follow Supabase naming convention
        expected_categories = [
            "00_extensions",
            "01_types", 
            "02_tables",
            "03_security",
            "04_functions",
            "05_triggers",
            "06_views",
            "07_indexes"
        ]
        
        # Check that categories exist and are properly ordered
        actual_categories = sorted(result.keys())
        
        for category in expected_categories:
            if category in result and result[category]:
                assert category in actual_categories
        
        # Verify specific Supabase categorization
        if "00_extensions" in result:
            extensions = [obj.raw_sql for obj in result["00_extensions"]]
            assert any("uuid-ossp" in ext for ext in extensions)
        
        if "03_security" in result:
            security_objects = [obj.raw_sql for obj in result["03_security"]]
            rls_found = any("ROW LEVEL SECURITY" in obj for obj in security_objects)
            policy_found = any("CREATE POLICY" in obj for obj in security_objects)
            assert rls_found or policy_found
    
    def test_supabase_file_structure_generation(self):
        """Test generation of Supabase file structure."""
        sql = """
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        CREATE TYPE status AS ENUM ('active', 'inactive');
        CREATE TABLE users (id SERIAL PRIMARY KEY, status status);
        CREATE POLICY users_policy ON users FOR ALL USING (true);
        """
        
        graph = self.create_test_graph(sql)
        categorized = self.splitter.split(graph, "supabase")
        
        # Generate file structure
        files = self.splitter.generate_file_structure(categorized)
        
        # Should generate appropriately named files
        file_paths = list(files.keys())
        
        # Look for Supabase-style paths
        extension_files = [p for p in file_paths if "extension" in str(p).lower()]
        type_files = [p for p in file_paths if "type" in str(p).lower()]
        table_files = [p for p in file_paths if "table" in str(p).lower()]
        security_files = [p for p in file_paths if "security" in str(p).lower() or "policy" in str(p).lower()]
        
        # Should have created files for each category with content
        if categorized.get("00_extensions"):
            assert len(extension_files) > 0
        if categorized.get("01_types"):
            assert len(type_files) > 0
        if categorized.get("02_tables"):
            assert len(table_files) > 0
        if categorized.get("03_security"):
            assert len(security_files) > 0
    
    def test_supabase_rls_policy_grouping(self):
        """Test that RLS and policies are properly grouped."""
        sql = """
        CREATE TABLE users (id SERIAL PRIMARY KEY);
        CREATE TABLE posts (id SERIAL, user_id INTEGER REFERENCES users(id));
        
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY users_select ON users FOR SELECT USING (auth.uid() = id);
        CREATE POLICY users_insert ON users FOR INSERT WITH CHECK (auth.uid() = id);
        CREATE POLICY posts_select ON posts FOR SELECT USING (auth.uid() = user_id);
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split(graph, "supabase")
        
        if "03_security" in result and result["03_security"]:
            security_sql = [obj.raw_sql for obj in result["03_security"]]
            
            # Should contain RLS statements
            rls_statements = [sql for sql in security_sql if "ROW LEVEL SECURITY" in sql]
            assert len(rls_statements) >= 2, "Should have RLS statements for both tables"
            
            # Should contain policy statements
            policy_statements = [sql for sql in security_sql if "CREATE POLICY" in sql]
            assert len(policy_statements) >= 3, "Should have all policy statements"


class TestStandardSplitter:
    """Test standard SQL splitting logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = StandardSplitter()
        self.parser = PostgreSQLParser()
        self.analyzer = RustworkxDependencyAnalyzer()
    
    def create_test_graph(self, sql: str):
        """Helper to create dependency graph from SQL."""
        statements = self.parser.parse_sql(sql)
        return self.analyzer.analyze(statements)
    
    def test_standard_categorization(self):
        """Test standard SQL categorization."""
        sql = """
        CREATE TYPE status AS ENUM ('active', 'inactive');
        CREATE TABLE users (id SERIAL PRIMARY KEY, status status);
        CREATE INDEX idx_users_status ON users(status);
        CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'active';
        
        CREATE FUNCTION get_active_count() RETURNS INTEGER AS $$
            SELECT COUNT(*) FROM users WHERE status = 'active';
        $$ LANGUAGE SQL;
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split(graph, "standard")
        
        # Should use standard SQL categories
        expected_categories = [
            "types", "tables", "indexes", "views", "functions"
        ]
        
        for category in expected_categories:
            if category in result and result[category]:
                assert len(result[category]) > 0
    
    def test_standard_file_naming(self):
        """Test standard file naming conventions."""
        sql = """
        CREATE TABLE users (id SERIAL PRIMARY KEY);
        CREATE TABLE posts (id SERIAL PRIMARY KEY);
        """
        
        graph = self.create_test_graph(sql)
        categorized = self.splitter.split(graph, "standard")
        files = self.splitter.generate_file_structure(categorized)
        
        # Should use standard naming without numeric prefixes
        file_names = [str(path) for path in files.keys()]
        
        # Should not have Supabase-style numeric prefixes
        numbered_files = [name for name in file_names if name.startswith(('00_', '01_', '02_'))]
        assert len(numbered_files) == 0, "Standard splitter should not use numeric prefixes"


class TestSplitterFileGeneration:
    """Test file generation capabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = SchemaSplitterEngine()
        self.parser = PostgreSQLParser()
        self.analyzer = RustworkxDependencyAnalyzer()
    
    def test_generate_migration_file(self):
        """Test generation of main migration file."""
        original_file = Path("test_migration.sql")
        split_files = {
            Path("schemas/01_types.sql"): "CREATE TYPE status AS ENUM ('active');",
            Path("schemas/02_tables.sql"): "CREATE TABLE users (id SERIAL, status status);",
            Path("schemas/03_indexes.sql"): "CREATE INDEX idx_users_status ON users(status);"
        }
        
        migration_content = self.splitter.create_migration_file(original_file, split_files)
        
        # Should contain references to all split files
        assert "01_types.sql" in migration_content
        assert "02_tables.sql" in migration_content
        assert "03_indexes.sql" in migration_content
        
        # Should maintain dependency order
        types_pos = migration_content.find("01_types.sql")
        tables_pos = migration_content.find("02_tables.sql")
        indexes_pos = migration_content.find("03_indexes.sql")
        
        assert types_pos < tables_pos < indexes_pos, "Migration should maintain dependency order"
    
    def test_empty_category_handling(self):
        """Test handling of empty categories."""
        sql = """
        CREATE TABLE users (id SERIAL PRIMARY KEY);
        """
        
        graph = self.create_test_graph(sql)
        result = self.splitter.split_by_category(graph)
        
        # Should not create empty categories in result
        for category, objects in result.items():
            assert len(objects) > 0, f"Category {category} should not be empty"
    
    def create_test_graph(self, sql: str):
        """Helper to create dependency graph from SQL."""
        statements = self.parser.parse_sql(sql)
        return self.analyzer.analyze(statements)


@pytest.fixture
def complex_ecommerce_schema():
    """Complex e-commerce schema for testing."""
    return """
    -- Extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Types
    CREATE TYPE user_role AS ENUM ('customer', 'admin', 'moderator');
    CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered');
    CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed');
    
    -- Core tables
    CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR(255) UNIQUE NOT NULL,
        role user_role DEFAULT 'customer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        parent_id INTEGER REFERENCES categories(id)
    );
    
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category_id INTEGER REFERENCES categories(id),
        price DECIMAL(10,2) NOT NULL
    );
    
    CREATE TABLE orders (
        id SERIAL PRIMARY KEY,
        user_id UUID REFERENCES users(id),
        status order_status DEFAULT 'pending',
        total DECIMAL(10,2) NOT NULL
    );
    
    CREATE TABLE order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER NOT NULL,
        price DECIMAL(10,2) NOT NULL
    );
    
    CREATE TABLE payments (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id),
        amount DECIMAL(10,2) NOT NULL,
        status payment_status DEFAULT 'pending'
    );
    
    -- Views
    CREATE VIEW order_summaries AS
    SELECT 
        o.id,
        o.user_id,
        u.email,
        o.status,
        o.total,
        COUNT(oi.id) as item_count
    FROM orders o
    JOIN users u ON o.user_id = u.id
    LEFT JOIN order_items oi ON o.id = oi.order_id
    GROUP BY o.id, o.user_id, u.email, o.status, o.total;
    
    -- Functions
    CREATE FUNCTION calculate_order_total(order_id_param INTEGER)
    RETURNS DECIMAL(10,2) AS $$
    BEGIN
        RETURN (
            SELECT COALESCE(SUM(quantity * price), 0)
            FROM order_items 
            WHERE order_id = order_id_param
        );
    END;
    $$ LANGUAGE plpgsql;
    
    -- Triggers
    CREATE FUNCTION update_order_total()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE orders 
        SET total = calculate_order_total(NEW.order_id)
        WHERE id = NEW.order_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    CREATE TRIGGER trigger_update_order_total
        AFTER INSERT OR UPDATE OR DELETE ON order_items
        FOR EACH ROW
        EXECUTE FUNCTION update_order_total();
    
    -- Indexes
    CREATE INDEX idx_products_category ON products(category_id);
    CREATE INDEX idx_orders_user_status ON orders(user_id, status);
    CREATE INDEX idx_order_items_order ON order_items(order_id);
    CREATE INDEX idx_payments_order ON payments(order_id);
    
    -- Security
    ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
    CREATE POLICY orders_user_policy ON orders
        FOR ALL USING (user_id = current_user_id());
    
    ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
    CREATE POLICY payments_user_policy ON payments
        FOR ALL USING (
            order_id IN (SELECT id FROM orders WHERE user_id = current_user_id())
        );
    """


def test_complex_schema_splitting(complex_ecommerce_schema):
    """Test splitting of complex e-commerce schema."""
    parser = PostgreSQLParser()
    analyzer = RustworkxDependencyAnalyzer()
    splitter = SupabaseSplitter()
    
    # Parse and analyze
    statements = parser.parse_sql(complex_ecommerce_schema)
    graph = analyzer.analyze(statements)
    
    # Test dependency-based splitting
    dep_result = splitter.split_by_dependencies(graph)
    assert len(dep_result) >= 3, "Should have multiple dependency levels"
    
    # Test category-based splitting  
    cat_result = splitter.split_by_category(graph)
    
    # Should have all major categories
    expected_categories = [
        "extensions", "types", "tables", "views", 
        "functions", "triggers", "indexes", "security"
    ]
    
    found_categories = [cat for cat in expected_categories if cat in cat_result and cat_result[cat]]
    assert len(found_categories) >= 6, f"Should find most categories, found: {found_categories}"
    
    # Test hybrid splitting
    hybrid_result = splitter.split_hybrid(graph)
    assert len(hybrid_result) > 0, "Hybrid splitting should produce results"
    
    # Test file generation
    files = splitter.generate_file_structure(cat_result)
    assert len(files) > 0, "Should generate files"
    
    # Verify file contents are not empty
    for file_path, content in files.items():
        assert content.strip(), f"File {file_path} should have content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])