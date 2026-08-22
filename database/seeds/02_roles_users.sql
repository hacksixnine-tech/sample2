-- ==============================================================================
-- PHANTOM SEED 02: Roles and Demo Users (RBAC)
-- ==============================================================================

-- Standard RBAC Roles
INSERT INTO roles (id, name, description, permissions) VALUES
('20000000-0000-0000-0000-000000000001', 'SYSTEM_ADMIN', 'Full statewide system administration and configuration', '["*"]'::jsonb),
('20000000-0000-0000-0000-000000000002', 'POLICE_OFFICER', 'Law enforcement officer with live tracking and alert acknowledgement privileges', '["cameras:view", "alerts:manage", "watchlist:read", "incidents:create", "incidents:update", "evidence:view", "tracking:execute"]'::jsonb),
('20000000-0000-0000-0000-000000000003', 'DEPARTMENT_OFFICER', 'Nodal officer for municipal or departmental camera integration', '["cameras:view_dept", "cameras:manage_dept", "health:view_dept"]'::jsonb),
('20000000-0000-0000-0000-000000000004', 'RTO_OFFICER', 'Motor Vehicles inspector for ANPR hotlist and traffic enforcement', '["anpr:search", "watchlist:manage_vehicles", "alerts:view"]'::jsonb),
('20000000-0000-0000-0000-000000000005', 'ANALYST', 'Crime intelligence analyst with trajectory and pattern analysis tools', '["analytics:read", "tracking:execute", "gis:query", "reports:generate"]'::jsonb),
('20000000-0000-0000-0000-000000000006', 'INVESTIGATOR', 'Lead case investigator managing incidents and forensic evidence dossiers', '["incidents:manage", "evidence:manage", "tracking:execute", "watchlist:read"]'::jsonb),
('20000000-0000-0000-0000-000000000007', 'AUDITOR', 'Independent oversight and regulatory compliance auditor', '["audit:read_all", "reports:generate"]'::jsonb),
('20000000-0000-0000-0000-000000000008', 'VIEWER', 'Read-only authorized observer for designated feeds', '["cameras:view_public", "gis:view_map"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Demo Users (Development Password Hashes: bcrypt placeholder for "Phantom@2026")
INSERT INTO users (id, username, email, password_hash, full_name, badge_number, phone_number, department_id, role_id, is_active) VALUES
('30000000-0000-0000-0000-000000000001', 'admin_phantom', 'admin@phantom.gujarat.gov.in.demo', '$2b$12$K8/9E...demo_bcrypt_hash_placeholder_for_phantom_2026', 'Rajesh Patel', 'ADM-001', '+91-9825000001', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', TRUE),
('30000000-0000-0000-0000-000000000002', 'dsp_ahmedabad', 'dsp.ahmedabad@police.gujarat.gov.in.demo', '$2b$12$K8/9E...demo_bcrypt_hash_placeholder_for_phantom_2026', 'Vikram Singh Jadeja', 'GJ-POL-4412', '+91-9825000002', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', TRUE),
('30000000-0000-0000-0000-000000000003', 'rto_inspector_gj01', 'inspector.gj01@rto.gujarat.gov.in.demo', '$2b$12$K8/9E...demo_bcrypt_hash_placeholder_for_phantom_2026', 'Amit Trivedi', 'RTO-GJ01-88', '+91-9825000003', '10000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000004', TRUE),
('30000000-0000-0000-0000-000000000004', 'analyst_cid', 'cid.analyst@police.gujarat.gov.in.demo', '$2b$12$K8/9E...demo_bcrypt_hash_placeholder_for_phantom_2026', 'Priya Desai', 'CID-ANA-109', '+91-9825000004', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000005', TRUE),
('30000000-0000-0000-0000-000000000005', 'inv_cybercell', 'investigator@cybercell.gujarat.gov.in.demo', '$2b$12$K8/9E...demo_bcrypt_hash_placeholder_for_phantom_2026', 'Dhaval Shah', 'CYBER-INV-301', '+91-9825000005', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000006', TRUE)
ON CONFLICT (username) DO NOTHING;
