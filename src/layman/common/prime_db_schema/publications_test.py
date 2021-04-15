import uuid
from test import process_client
import pytest

from layman import settings, app as app, LaymanError
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

userinfo_baseline = {"issuer_id": 'mock_test_publications_test',
                     "claims": {"email": "test@liferay.com",
                                "preferred_username": 'test_preferred',
                                "name": "test ensure user",
                                "given_name": "test",
                                "family_name": "user",
                                "middle_name": "ensure",
                                }
                     }


def test_publication_basic():
    def publications_by_type(prefix,
                             publication_type,
                             style_type,
                             ):
        username = prefix + '_username'
        publication_name = prefix + '_pub_name'
        publication_title = prefix + '_pub_ Title'
        publication_title2 = prefix + '_pub_ Title2'

        with app.app_context():
            workspaces.ensure_workspace(username)
            uuid_orig = uuid.uuid4()
            uuid_str = str(uuid_orig)
            db_info = {"name": publication_name,
                       "title": publication_title,
                       "publ_type_name": publication_type,
                       "uuid": uuid_orig,
                       "actor_name": username,
                       'style_type': style_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
                       }
            publications.insert_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == str(uuid_str)

            db_info = {"name": publication_name,
                       "title": publication_title2,
                       "actor_name": username,
                       "publ_type_name": publication_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
                       'style_type': style_type,
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title2
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            db_info = {"name": publication_name,
                       "title": publication_title,
                       "actor_name": username,
                       "publ_type_name": publication_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
                       'style_type': style_type,
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            publications.delete_publication(username, publication_type, publication_name)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs.get((username, publication_type, publication_name)) is None

            workspaces.delete_workspace(username)

    publications_by_type('test_publication_basic_layer',
                         LAYER_TYPE,
                         'sld',
                         )
    publications_by_type('test_publication_basic_map',
                         MAP_TYPE,
                         None,
                         )


class TestSelectPublicationsBasic:
    workspace1 = 'test_select_publications_basic_workspace1'
    workspace2 = 'test_select_publications_basic_workspace2'
    qml_style_file = 'sample/style/small_layer.qml'
    publications = [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le', dict()),
                    (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml', {'style_file': qml_style_file}),
                    (workspace1, MAP_TYPE, 'test_select_publications_publication1me', dict()),
                    (workspace2, LAYER_TYPE, 'test_select_publications_publication2le', dict()),
                    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        for publication in self.publications:
            process_client.publish_workspace_publication(publication[1], publication[0], publication[2], **publication[3])
        yield
        for publication in self.publications:
            process_client.delete_workspace_publication(publication[1], publication[0], publication[2])

    @staticmethod
    @pytest.mark.parametrize('query_params, expected_publications', [
        ({'workspace_name': workspace1, 'pub_type': LAYER_TYPE},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
          (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
          ]),
        ({'workspace_name': workspace1, 'pub_type': MAP_TYPE}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1me'), ]),
        ({'workspace_name': workspace1, 'style_type': 'qml'},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'), ]),
        ({'workspace_name': workspace1, 'style_type': 'sld'},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'), ]),
        ({'workspace_name': workspace1}, [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
                                          (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
                                          (workspace1, MAP_TYPE, 'test_select_publications_publication1me'),
                                          ]),
        (dict(), [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
                  (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
                  (workspace1, MAP_TYPE, 'test_select_publications_publication1me'),
                  (workspace2, LAYER_TYPE, 'test_select_publications_publication2le'),
                  ]),
    ])
    @pytest.mark.usefixtures('ensure_layman', 'provide_data')
    def test_get_publications(query_params, expected_publications):
        with app.app_context():
            infos = publications.get_publication_infos(**query_params)
        info_publications = list(infos.keys())
        assert expected_publications == info_publications


class TestSelectPublicationsComplex:
    workspace1 = 'test_select_publications_complex_workspace1'
    workspace2 = 'test_select_publications_complex_workspace2'

    map_1e_2_4x6_6 = 'test_select_publications_map1e'
    map_1e_3_3x3_3 = 'test_select_publications_map1e_3_3x3_3'
    map_1o_2_2x3_6 = 'test_select_publications_map1o'
    map_1oe_3_7x5_9 = 'test_select_publications_map1oe'
    map_2e_3_3x5_5 = 'test_select_publications_map2e'
    map_2o_2_2x4_4 = 'test_select_publications_map2o'

    publications = [
        (workspace1, MAP_TYPE, map_1e_2_4x6_6,
         {'title': 'Příliš žluťoučký Kůň úpěl ďábelské ódy',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {settings.RIGHTS_EVERYONE_ROLE}},
          'bbox': (2000, 4000, 6000, 6000),
          }),
        (workspace1, MAP_TYPE, map_1e_3_3x3_3,
         {'title': 'Jednobodová vrstva',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {settings.RIGHTS_EVERYONE_ROLE}},
          'bbox': (3000, 3000, 3000, 3000),
          }),
        (workspace1, MAP_TYPE, map_1o_2_2x3_6,
         {'title': 'Ďůlek kun Karel',
          'access_rights': {'read': {workspace1},
                            'write': {workspace1}},
          'bbox': (2000, 2000, 3000, 6000),
          }),
        (workspace1, MAP_TYPE, map_1oe_3_7x5_9,
         {'title': 'jedna dva tři čtyři',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {workspace1}},
          'bbox': (3000, 7000, 5000, 9000),
          }),
        (workspace2, MAP_TYPE, map_2e_3_3x5_5,
         {'title': 'Svíčky is the best game',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {settings.RIGHTS_EVERYONE_ROLE}},
          'bbox': (3000, 3000, 5000, 5000),
          }),
        (workspace2, MAP_TYPE, map_2o_2_2x4_4,
         {'title': 'druhá mapa JeDnA óda',
          'access_rights': {'read': {workspace2},
                            'write': {workspace2}},
          'bbox': (2000, 2000, 4000, 4000),
          }),
    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        with app.app_context():
            for idx, ws in enumerate([self.workspace1, self.workspace2]):
                ws_id = workspaces.ensure_workspace(ws)
                userinfo = {
                    'sub': idx + 1,
                    'issuer_id': 'layman',
                    'claims': {
                        'email': f"{ws}@liferay.com",
                        'name': ws,
                        'middle_name': '',
                        'family_name': ws,
                        'given_name': ws,
                        'preferred_username': ws,
                    }
                }
                users.ensure_user(ws_id, userinfo)

            for workspace, publ_type, publ_name, publ_info in self.publications:
                publications.insert_publication(workspace, {
                    'name': publ_name,
                    'title': publ_info['title'],
                    'publ_type_name': publ_type,
                    'uuid': uuid.uuid4(),
                    'actor_name': workspace,
                    'style_type': 'sld',
                    'access_rights': publ_info['access_rights'],
                })
                publications.set_bbox(workspace, publ_type, publ_name, publ_info['bbox'])
        yield
        with app.app_context():
            for workspace, publ_type, publ_name, _ in self.publications:
                publications.delete_publication(workspace, publ_type, publ_name)

    @staticmethod
    @pytest.mark.parametrize('query_params, expected_publications', [
        (dict(), [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                  (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                  (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                  (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                  (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                  (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                  ]),
        ({'reader': settings.ANONYM_USER}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                            (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                                            (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                                            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                                            ]),
        ({'reader': workspace2}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                  (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                                  (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                                  (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                                  (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                                  ]),
        ({'writer': settings.ANONYM_USER}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                            (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                                            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                                            ]),
        ({'writer': workspace2}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                  (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                                  (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                                  (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                                  ]),
        ({'full_text_filter': 'dva'}, [(workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                                       ]),
        ({'full_text_filter': 'games'}, [(workspace2, MAP_TYPE, map_2e_3_3x5_5),
                                         ]),
        ({'full_text_filter': 'kun'}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                       (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                                       ]),
        ({'full_text_filter': 'jedna'}, [(workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                                         (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                                         ]),
        ({'full_text_filter': 'upet'}, []),
        ({'full_text_filter': 'dva | kun'}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                             (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                                             (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                                             ]),
        ({'full_text_filter': 'kun & ody'}, [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                                             ]),
        ({'order_by_list': ['full_text'], 'ordering_full_text': 'jedna'}, [
            (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
            (workspace2, MAP_TYPE, map_2o_2_2x4_4),
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
            (workspace1, MAP_TYPE, map_1e_3_3x3_3),
            (workspace1, MAP_TYPE, map_1o_2_2x3_6),
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
        ]),
        ({'full_text_filter': 'dva | kun', 'order_by_list': ['full_text'], 'ordering_full_text': 'karel | kun'}, [
            (workspace1, MAP_TYPE, map_1o_2_2x3_6),
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
            (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
        ]),
        ({'order_by_list': ['title'], }, [
            (workspace2, MAP_TYPE, map_2o_2_2x4_4),
            (workspace1, MAP_TYPE, map_1o_2_2x3_6),
            (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
            (workspace1, MAP_TYPE, map_1e_3_3x3_3),
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
        ]),
        ({'order_by_list': ['last_change'], }, [
            (workspace2, MAP_TYPE, map_2o_2_2x4_4),
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
            (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
            (workspace1, MAP_TYPE, map_1o_2_2x3_6),
            (workspace1, MAP_TYPE, map_1e_3_3x3_3),
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
        ]),
        ({'order_by_list': ['bbox'], 'ordering_bbox': (2999, 2999, 5001, 5001), }, [
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
            (workspace2, MAP_TYPE, map_2o_2_2x4_4),
            (workspace1, MAP_TYPE, map_1o_2_2x3_6),
            (workspace1, MAP_TYPE, map_1e_3_3x3_3),
            (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
        ]),
        ({'order_by_list': ['bbox'], 'ordering_bbox': (4001, 4001, 4001, 4001),
          'bbox_filter': (4001, 4001, 4001, 4001), }, [
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
        ]),
        ({'bbox_filter': (3001, 3001, 4999, 4999),
          }, [
            (workspace1, MAP_TYPE, map_1e_2_4x6_6),
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
            (workspace2, MAP_TYPE, map_2o_2_2x4_4),
        ]),
        ({'bbox_filter': (3001, 3001, 3001, 3001),
          }, [
            (workspace2, MAP_TYPE, map_2e_3_3x5_5),
            (workspace2, MAP_TYPE, map_2o_2_2x4_4),
        ]),
    ])
    @pytest.mark.usefixtures('provide_data')
    def test_get_publications(query_params, expected_publications):
        with app.app_context():
            infos = publications.get_publication_infos(**query_params)
        info_publications = list(infos.keys())
        assert set(expected_publications) == set(info_publications)
        assert expected_publications == info_publications


def test_only_valid_names():
    workspace_name = 'test_only_valid_names_workspace'
    username = 'test_only_valid_names_user'

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '10'
        users.ensure_user(id_workspace_user, userinfo)

        publications.only_valid_names(set())
        publications.only_valid_names({username, })
        publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, })
        publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, username, })
        publications.only_valid_names({username, settings.RIGHTS_EVERYONE_ROLE, })

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({username, workspace_name})
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({workspace_name, username})
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({workspace_name, settings.RIGHTS_EVERYONE_ROLE, })
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, 'skaljgdalskfglshfgd', })
        assert exc_info.value.code == 43

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


def test_at_least_one_can_write():
    workspace_name = 'test_at_least_one_can_write_workspace'
    username = 'test_at_least_one_can_write_user'

    publications.at_least_one_can_write({username, })
    publications.at_least_one_can_write({settings.RIGHTS_EVERYONE_ROLE, })
    publications.at_least_one_can_write({username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.at_least_one_can_write({workspace_name, })
    publications.at_least_one_can_write({'lusfjdiaurghalskug', })

    with pytest.raises(LaymanError) as exc_info:
        publications.at_least_one_can_write(set())
    assert exc_info.value.code == 43


def test_who_can_write_can_read():
    workspace_name = 'test_who_can_write_can_read_workspace'
    username = 'test_who_can_write_can_read_user'

    publications.who_can_write_can_read(set(), set())
    publications.who_can_write_can_read({username, }, {username, })
    publications.who_can_write_can_read({username, workspace_name}, {username, })
    publications.who_can_write_can_read({username, settings.RIGHTS_EVERYONE_ROLE}, {username, })
    publications.who_can_write_can_read({username, settings.RIGHTS_EVERYONE_ROLE}, {username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, username, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, workspace_name, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, username, }, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, username, }, set())
    publications.who_can_write_can_read({workspace_name, }, {workspace_name, })

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {workspace_name, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {username, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {settings.RIGHTS_EVERYONE_ROLE, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(username, {settings.RIGHTS_EVERYONE_ROLE, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(username, {workspace_name, })
    assert exc_info.value.code == 43


def test_i_can_still_write():
    workspace_name = 'test_i_can_still_write_workspace'
    username = 'test_who_can_write_can_read_user'

    publications.i_can_still_write(None, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(None, {username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {workspace_name, settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {workspace_name, username, })

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(None, set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(None, {workspace_name, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, {workspace_name, })
    assert exc_info.value.code == 43


def test_owner_can_still_write():
    workspace_name = 'test_owner_can_still_write_workspace'
    username = 'test_owner_can_still_write_user'

    publications.owner_can_still_write(None, set())
    publications.owner_can_still_write(None, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.owner_can_still_write(None, {username, })
    publications.owner_can_still_write(username, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.owner_can_still_write(username, {username, })
    publications.owner_can_still_write(username, {username, workspace_name, })

    with pytest.raises(LaymanError) as exc_info:
        publications.owner_can_still_write(username, set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.owner_can_still_write(username, {workspace_name, })
    assert exc_info.value.code == 43


def test_clear_roles():
    workspace_name = 'test_clear_roles_workspace'
    username = 'test_clear_roles_user'

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '20'
        users.ensure_user(id_workspace_user, userinfo)

        list = publications.clear_roles({username, }, workspace_name)
        assert list == {username, }, list

        list = publications.clear_roles({username, workspace_name, }, workspace_name)
        assert list == {username, workspace_name, }, list

        list = publications.clear_roles({username, }, username)
        assert list == set(), list

        list = publications.clear_roles({username, workspace_name, }, username)
        assert list == {workspace_name, }, list

        list = publications.clear_roles({username, settings.RIGHTS_EVERYONE_ROLE, }, workspace_name)
        assert list == {username, }, list

        list = publications.clear_roles({username, settings.RIGHTS_EVERYONE_ROLE, }, username)
        assert list == set(), list

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


def assert_access_rights(workspace_name,
                         publication_name,
                         publication_type,
                         read_to_test,
                         write_to_test):
    pubs = publications.get_publication_infos(workspace_name, publication_type)
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["read"] == read_to_test
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["write"] == write_to_test


def test_insert_rights():
    def case_test_insert_rights(username,
                                publication_info_original,
                                access_rights,
                                read_to_test,
                                write_to_test,
                                ):
        publication_info = publication_info_original.copy()
        publication_info.update({"access_rights": access_rights})
        if users.get_user_infos(username):
            publication_info.update({"actor_name": username})
        publications.insert_publication(username, publication_info)
        assert_access_rights(username,
                             publication_info_original["name"],
                             publication_info_original["publ_type_name"],
                             read_to_test,
                             write_to_test,
                             )
        publications.delete_publication(username, publication_info["publ_type_name"], publication_info["name"])

    workspace_name = 'test_insert_rights_workspace'
    username = 'test_insert_rights_user'
    username2 = 'test_insert_rights_user2'

    publication_name = 'test_insert_rights_publication_name'
    publication_type = MAP_TYPE

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '30'
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '40'
        users.ensure_user(id_workspace_user2, userinfo)

        publication_info = {"name": publication_name,
                            "title": publication_name,
                            "actor_name": username,
                            "publ_type_name": publication_type,
                            "uuid": uuid.uuid4(),
                            }

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, },
                                 "write": {username, },
                                 },
                                [username, ],
                                [username, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, username2, },
                                 "write": {username, username2, },
                                 },
                                [username, username2, ],
                                [username, username2, ],
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                [settings.RIGHTS_EVERYONE_ROLE, ],
                                [settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        users.delete_user(username)
        users.delete_user(username2)
        workspaces.delete_workspace(workspace_name)


def test_update_rights():
    def case_test_update_rights(username,
                                publication_info_original,
                                publication_update_info,
                                read_to_test,
                                write_to_test,
                                ):
        if not publication_update_info.get("publ_type_name"):
            publication_update_info["publ_type_name"] = publication_info_original["publ_type_name"]
        if not publication_update_info.get("name"):
            publication_update_info["name"] = publication_info_original["name"]
        publications.update_publication(username,
                                        publication_update_info,
                                        )
        assert_access_rights(username,
                             publication_info_original["name"],
                             publication_info_original["publ_type_name"],
                             read_to_test,
                             write_to_test,
                             )

    workspace_name = 'test_update_rights_workspace'
    username = 'test_update_rights_user'
    username2 = 'test_update_rights_user2'

    publication_name = 'test_update_rights_publication_name'
    publication_type = MAP_TYPE
    publication_insert_info = {"name": publication_name,
                               "title": publication_name,
                               "publ_type_name": publication_type,
                               "actor_name": username,
                               "uuid": uuid.uuid4(),
                               "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                 },
                               }

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '50'
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '60'
        users.ensure_user(id_workspace_user2, userinfo)

        publications.insert_publication(username, publication_insert_info)

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, username2, },
                                                   "write": {username, username2, },
                                                   },
                                 'actor_name': username},
                                [username, username2, ],
                                [username, username2, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                [username, ],
                                [username, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': None},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username2, },
                                                       "write": {username2, },
                                                       },
                                     'actor_name': username2},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
        assert exc_info.value.code == 43

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                [username, ],
                                [username, ],
                                )
        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {username, username2, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, username2, ],
                                    )
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [settings.RIGHTS_EVERYONE_ROLE, ],
                                    )
        assert exc_info.value.code == 43

        publications.delete_publication(username, publication_insert_info["publ_type_name"], publication_insert_info["name"])
        users.delete_user(username)
        users.delete_user(username2)
        workspaces.delete_workspace(workspace_name)


@pytest.mark.usefixtures('ensure_layman')
def test_publications_same_name():
    publ_name = 'test_publications_same_name_publ'
    username = 'test_publications_same_name_user'
    username2 = 'test_publications_same_name_user2'

    process_client.publish_workspace_layer(username, publ_name)
    process_client.publish_workspace_map(username, publ_name)
    process_client.publish_workspace_layer(username2, publ_name)
    process_client.publish_workspace_map(username2, publ_name)

    with app.app_context():
        pubs = publications.get_publication_infos(username)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos(username2)
        assert len(pubs) == 2
        pubs = publications.get_publication_infos()
        assert len(pubs) >= 4

    process_client.delete_workspace_layer(username, publ_name)
    process_client.delete_workspace_map(username, publ_name)
    process_client.delete_workspace_layer(username2, publ_name)
    process_client.delete_workspace_map(username2, publ_name)
