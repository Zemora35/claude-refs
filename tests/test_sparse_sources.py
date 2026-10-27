"""Sparse reference fetching must not expand downloads or run LFS hooks."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sparse_sources', ROOT/'scripts/sync_sources.py')
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

class SparseSourcesTests(unittest.TestCase):
    def test_invalid_patterns_fail_before_any_git_or_filesystem_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            for bad in ['../escape','/absolute','C:/escape','docs/*','!README.md','.GIT/config','docs\nsecret','docs\\secret']:
                with self.subTest(path=bad),patch.object(sync,'git') as git:
                    with self.assertRaises(ValueError):
                        sync.source_record(root,{'repository':'fixture/source','commit':'a'*40,'sparse_paths':[bad]})
                    git.assert_not_called()
                    self.assertEqual(list(root.iterdir()),[])

    def test_sparse_patterns_exist_before_checkout_and_only_requested_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();target=root/'.sources/fixture_source'
            def fake_git(folder,*args):
                if args[0]=='init':(target/'.git/info').mkdir(parents=True)
                if args[0]=='checkout':
                    patterns=(target/'.git/info/sparse-checkout').read_text(encoding='utf-8')
                    self.assertEqual(patterns,'/README.md\n/skills/demo/SKILL.md\n')
                    (target/'README.md').write_text('fixture')
                    (target/'skills/demo').mkdir(parents=True)
                    (target/'skills/demo/SKILL.md').write_text('fixture')
                return 'a'*40 if args[0]=='rev-parse' else ''
            with patch.object(sync,'git',side_effect=fake_git):
                r=sync.source_record(root,{'repository':'fixture/source','commit':'a'*40,
                    'sparse_paths':['README.md','skills/demo/SKILL.md'],'checkout_scope':'documentation-and-skills'})
            self.assertTrue(r['matches_lock'])
            self.assertEqual(r['checkout_scope'],'documentation-and-skills')

    def test_git_disables_lfs_and_interactive_credentials(self):
        with tempfile.TemporaryDirectory() as temporary,patch.object(sync,'PACKAGE',Path(temporary)),patch.object(sync.subprocess,'run') as run:
            (Path(temporary)/'scripts').mkdir()
            run.return_value.returncode=0;run.return_value.stdout='ok'
            sync.git(None,'version')
            self.assertEqual(run.call_args.kwargs['env']['GIT_LFS_SKIP_SMUDGE'],'1')
            self.assertEqual(run.call_args.kwargs['env']['GIT_TERMINAL_PROMPT'],'0')

if __name__=='__main__':unittest.main()
