import unittest


class SchemaTests(unittest.TestCase):
    def test_action_schema_is_serializable(self):
        from imgtools.service.registry import get_tool
        from imgtools.service.schemas import action_schema

        schema = action_schema(get_tool("pdf.render_page"))

        self.assertEqual(schema["action"], "pdf.render_page")
        self.assertIn("params", schema)
        self.assertIn("result", schema)
        self.assertEqual(schema["result"]["type"], "object")

    def test_result_schema_documents_required_fields(self):
        from imgtools.service.schemas import result_schema

        schema = result_schema()

        self.assertIn("ok", schema["required"])
        self.assertIn("action", schema["required"])
        self.assertIn("outputs", schema["properties"])
        self.assertIn("warnings", schema["properties"])


if __name__ == "__main__":
    unittest.main()

