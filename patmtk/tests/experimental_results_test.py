import os
import json
import pytest


from results import ExperimentalResults
from results.experimental_results import TrackedKernel, RoundTripDecoder

from patm.modeling import Experiment


@pytest.fixture(scope='module')
def json_path(collections_root_dir, test_collection_name):
    return os.path.join(collections_root_dir, test_collection_name, 'results', 'exp-results-test-model_1.json')


@pytest.fixture(scope='module')
def kernel_data_0():
    return [
        [[1, 2], [3, 4], [5, 6], [120, 100]],
        {'t01': {'coherence': [1, 2, 3],
                 'contrast': [6, 3],
                 'purity': [1, 8]},
         't00': {'coherence': [10, 2, 3],
                 'contrast': [67, 36],
                 'purity': [12, 89]},
         't02': {'coherence': [10, 11],
                 'contrast': [656, 32],
                 'purity': [17, 856]}}
    ]


@pytest.fixture(scope='module')
def kernel_object_0(kernel_data_0):
    return TrackedKernel(*kernel_data_0)


@pytest.fixture(scope='module')
def kernel_data_1():
    return [[[10,20], [30,40], [50,6], [80, 90]], {'t01': {'coherence': [3, 9],
                                                             'contrast': [96, 3],
                                                             'purity': [1, 98]},
                                                     't00': {'coherence': [19,2,93],
                                                             'contrast': [7, 3],
                                                             'purity': [2, 89]},
                                                     't02': {'coherence': [0,11],
                                                             'contrast': [66, 32],
                                                             'purity': [17, 85]}
                                                     }]


@pytest.fixture(scope='module')
def exp_res_obj1(kernel_data_0, kernel_data_1, json_path, test_collection_dir):

    exp = ExperimentalResults.from_dict({
        'scalars': {
            'dir': 'a-dataset-dir',
            'label': 'a-model-label',
            'dataset_iterations': 3,  # LEGACY '_' (underscore) usage
            'nb_topics': 5,  # LEGACY '_' (underscore) usage
            'document_passes': 2,  # LEGACY '_' (underscore) usage
            'background_topics': ['t0', 't1'],  # LEGACY '_' (underscore) usage
            'domain_topics': ['t2', 't3', 't4'],  # LEGACY '_' (underscore) usage
            'modalities': {'dcn': 1, 'icn': 5}
        },
        'tracked': {
            'perplexity': [1, 2, 3],
            'sparsity-phi-@dc': [-2, -4, -6],
            'sparsity-phi-@ic': [-56, -12, -32],
            'sparsity-theta': [2, 4, 6],
            'background-tokens-ratio-0.3': [0.4, 0.3, 0.2],
            'topic-kernel': {
                '0.60': {
                    'avg_coh': kernel_data_0[0][0],
                    'avg_con': kernel_data_0[0][1],
                    'avg_pur': kernel_data_0[0][2],
                    'size': kernel_data_0[0][3],
                    'topics': kernel_data_0[1]
                },
                '0.80': {
                    'avg_coh': kernel_data_1[0][0],
                    'avg_con': kernel_data_1[0][1],
                    'avg_pur': kernel_data_1[0][2],
                    'size': kernel_data_1[0][3],
                    'topics': kernel_data_1[1]
                }
            },
            'top-tokens': {
                '10': {
                    'avg_coh': [5, 6, 7],
                    'topics': {'t01': [12, 22, 3], 't00': [10, 2, 3], 't02': [10, 11]}
                },
                '100': {
                    'avg_coh': [10, 20, 30],
                    'topics': {'t01': [5, 7, 9], 't00': [12, 32, 3], 't02': [11, 1]}
                }
            },
            'tau-trajectories': {'phi': [1, 2, 3], 'theta': [5, 6, 7]},
            'regularization-dynamic-parameters': {'type-a': {'tau': [1, 2, 3]},
                                                  'type-b': {'tau': [-1, -1, -2], 'alpha': [1, 1.2]}},
            'collection-passes': [3]
        },
        'final': {
            'topic-kernel': {
                '0.60': {'t00': ['a', 'b', 'c'],
                         't01': ['d', 'e', 'f'],
                         't02': ['g', 'h', 'i']},
                '0.80': {'t00': ['j', 'k', 'l'],
                         't01': ['m', 'n', 'o'],
                         't02': ['p', 'q', 'r']}
            },
            'top-tokens': {
                '10': {
                    't00': ['s', 't', 'u'],
                    't01': ['v', 'x', 'y'],
                    't02': ['z', 'a1', 'b1']
                },
                '100': {
                    't00': ['c1', 'd1', 'e1'],
                    't01': ['f1', 'g1', 'h1'],
                    't02': ['i1', 'j1', 'k1']
                }
            },
            'background-tokens': ['l1', 'm1', 'n1']
        },
        'regularizers': ['reg1_params_pformat', 'reg2_params_pformat'],
        'reg_defs': {'type-a': 'reg1', 'type-b': 'reg2'},
        'score_defs': {'perplexity': 'prl', 'top-tokens-10': 'top10'}
    })

    if not os.path.isdir(os.path.join(test_collection_dir, 'results')):
        os.mkdir(os.path.join(test_collection_dir, 'results'))
    exp.save_as_json(json_path)
    return exp


class TestExperimentalResults(object):

    def test_tracked_kernel(self, kernel_object_0):
        assert kernel_object_0.average.contrast.all == [3, 4]
        assert kernel_object_0.average.purity.last == 6
        assert kernel_object_0.average.coherence.all == [1, 2]
        assert kernel_object_0.t00.contrast.all == [67, 36]
        assert kernel_object_0.t02.purity.all == [17, 856]
        assert kernel_object_0.t01.coherence.last == 3

    def test_constructor(self, exp_res_obj1):
        self._assert_experimental_results_creation(exp_res_obj1)

    def test_json_construction(self, exp_res_obj1):
        json_string = exp_res_obj1.to_json()
        res = json.loads(json_string, cls=RoundTripDecoder)
        assert res['scalars']['dir'] == 'a-dataset-dir'
        assert res['scalars']['domain_topics'] == ['t2', 't3', 't4']
        assert res['scalars']['modalities'] == {'dcn': 1, 'icn': 5}
        assert res['tracked']['perplexity'] == [1, 2, 3]
        assert res['tracked']['top-tokens']['10']['avg_coh'] == [5, 6, 7]
        assert res['tracked']['top-tokens']['10']['topics']['t01'] == [12, 22, 3]
        assert res['tracked']['top-tokens']['10']['topics']['t02'] == [10, 11]
        assert res['tracked']['topic-kernel']['0.60']['avg_pur'] == [5, 6]
        assert res['tracked']['topic-kernel']['0.60']['topics']['t00']['purity'] == [12, 89]
        assert res['tracked']['topic-kernel']['0.60']['topics']['t01']['contrast'] == [6, 3]
        assert res['tracked']['topic-kernel']['0.60']['topics']['t02']['coherence'] == [10, 11]
        assert res['tracked']['background-tokens-ratio-0.30'] == [0.4, 0.3, 0.2]
        assert res['tracked']['tau-trajectories']['phi'] == [1, 2, 3]
        assert res['tracked']['tau-trajectories']['theta'] == [5, 6, 7]
        assert res['final']['topic-kernel']['0.60']['t00'] == ['a', 'b', 'c']
        assert res['final']['topic-kernel']['0.60']['t02'] == ['g', 'h', 'i']
        assert res['final']['topic-kernel']['0.80']['t01'] == ['m', 'n', 'o']
        assert res['final']['top-tokens']['10']['t02'] == ['z', 'a1', 'b1']
        assert res['final']['top-tokens']['100']['t00'] == ['c1', 'd1', 'e1']
        assert res['final']['top-tokens']['100']['t01'] == ['f1', 'g1', 'h1']
        assert res['final']['background-tokens'] == ['l1', 'm1', 'n1']

    def test_creation_from_json(self, json_path):
        exp1 = ExperimentalResults.create_from_json_file(json_path)
        self._assert_experimental_results_creation(exp1)

    def test_creation_from_experiment(self, trained_model_n_experiment, train_settings):
        model, experiment = trained_model_n_experiment
        exp_res = ExperimentalResults.create_from_experiment(experiment)
        self._exp_res_obj_assertions(exp_res, experiment, train_settings)
        self._assert_tokens_loading_correctness(experiment, exp_res)

    def test_attributes(self, exp_res_obj1):
        # assert hasattr(exp_res_obj1.track, 'top10')
        assert hasattr(exp_res_obj1.tracked, 'top_tokens_100')
        assert hasattr(exp_res_obj1.tracked, 'top100')
        assert getattr(exp_res_obj1, 'top1000', 2) == 2
        assert getattr(exp_res_obj1.tracked, 'top100') == exp_res_obj1.tracked.top_100 == exp_res_obj1.tracked.top_tokens_100
        with(pytest.raises(AttributeError)):
            _ = exp_res_obj1.tracked.dibou

        with(pytest.raises(AttributeError)):
            _ = exp_res_obj1.a

    # @pytest.mark.skip()
    def test_loaded_model(self, loaded_model_n_experiment, train_settings):
        model, experiment = loaded_model_n_experiment
        exp_res = ExperimentalResults.create_from_experiment(experiment)
        self._exp_res_obj_assertions(exp_res, experiment, train_settings)

    def test_experimental_results_equality(self, trained_model_n_experiment):
        exp = trained_model_n_experiment[1]
        exp.save_experiment(save_phi=True)
        json_file = exp.train_results_handler.saved[-1]
        exp_res1 = ExperimentalResults.create_from_experiment(exp)
        exp_res2 = ExperimentalResults.create_from_json_file(json_file)
        assert exp_res1.scalars == exp_res2.scalars
        assert exp_res1.regularizers == exp_res2.regularizers
        assert exp_res1.reg_defs == exp_res2.reg_defs
        assert exp_res1.score_defs == exp_res2.score_defs
        assert sorted(exp_res1.final.background_tokens) == sorted(exp_res2.final.background_tokens)
        assert sorted(exp_res1.final.kernel_hash.keys()) == sorted(exp_res2.final.kernel_hash.keys())
        assert sorted(exp_res1.final.top_hash.keys()) ==  sorted(exp_res2.final.top_hash.keys())

        assert dir(exp_res1.tracked) == dir(exp_res2.tracked)

    def _exp_res_obj_assertions(self, exp_res, experiment, training_settings):
        col_passes = int(training_settings['learning']['collection_passes'])

        assert hasattr(exp_res, 'tracked')
        assert hasattr(exp_res, 'scalars')
        assert exp_res.scalars.nb_topics == int(training_settings['learning']['nb_topics'])
        assert exp_res.scalars.model_label == experiment.topic_model.label
        assert all(map(lambda x: len(x) == col_passes,
                       [exp_res.tracked.perplexity, exp_res.tracked.sparsity_theta, exp_res.tracked.sparsity_phi_d,
                        exp_res.tracked.sparsity_phi_i]))
        for reg_def in (_ for _ in training_settings['scores'] if _.startswith('topic-kernel-')):
            tr_kernel = getattr(exp_res.tracked, 'kernel' + reg_def.split('-')[-1][2:])
            assert all(
                map(lambda x: len(getattr(tr_kernel.average, x)) == col_passes, ['coherence', 'contrast', 'purity']))
        assert all(map(lambda x: len(x.average_coherence) == col_passes,
                       (getattr(exp_res.tracked, 'top' + _.split('-')[-1]) for _ in training_settings['scores'] if
                        _.startswith('top-tokens-'))))
        assert all(map(lambda x: len(x.all) == col_passes,
                       (getattr(exp_res.tracked, 'sparsity_phi_' + _.split('-')[-1][1]) for _ in
                        training_settings['scores'] if
                        _.startswith('sparsity-phi-@'))))

        for reg_def in (_ for _ in training_settings['scores'] if _.startswith('top-tokens-')):
            tr_top = getattr(exp_res.tracked, 'top' + reg_def.split('-')[-1])
            assert len(tr_top.average_coherence) == col_passes

    def _assert_tokens_loading_correctness(self, experiment, exp_res):
        """Requires a a model that has been trained (not just loaded) so that artm_model has correct state from score_tracker"""
        for kernel, kernel_def in zip(exp_res.final.kernels, exp_res.final.kernel_defs):
            for topic_name in exp_res.scalars.domain_topics:
                assert getattr(getattr(exp_res.final, kernel), topic_name).tokens == \
                       experiment.topic_model.artm_model.score_tracker[experiment.topic_model.definition2evaluator_name[kernel_def]].tokens[-1][topic_name]

    def _assert_experimental_results_creation(self, exp_obj):
        assert exp_obj.scalars.nb_topics == 5
        assert exp_obj.scalars.document_passes == 2
        assert exp_obj.tracked.perplexity.last == 3
        assert exp_obj.tracked.perplexity.all == [1, 2, 3]
        assert exp_obj.tracked.sparsity_phi_d.all == [-2, -4, -6]
        assert exp_obj.tracked.sparsity_phi_i.all == [-56, -12, -32]
        assert exp_obj.tracked.sparsity_theta.last == 6

        assert exp_obj.tracked.kernel6.average.purity.all == [5, 6]
        assert exp_obj.tracked.kernel6.t02.coherence.all == [10, 11]
        assert exp_obj.tracked.kernel6.t02.purity.all == [17, 856]
        assert exp_obj.tracked.kernel6.t02.contrast.last == 32
        assert exp_obj.tracked.kernel6.average.coherence.all == [1, 2]
        assert exp_obj.tracked.kernel8.average.purity.all == [50, 6]
        assert exp_obj.tracked.kernel8.t02.coherence.last == 11
        assert exp_obj.tracked.kernel8.t02.purity.all == [17, 85]
        assert exp_obj.tracked.kernel8.t00.contrast.last == 3
        assert exp_obj.tracked.kernel8.average.purity.last == 6

        assert exp_obj.tracked.top10.t01.all == [12, 22, 3]
        assert exp_obj.tracked.top10.t00.last == 3
        assert exp_obj.tracked.top10.average_coherence.all == [5, 6, 7]

        assert exp_obj.tracked.tau_trajectories.phi.all == [1, 2, 3]
        assert exp_obj.tracked.tau_trajectories.theta.last == 7

        assert exp_obj.final.kernel6.t00.tokens == ['a', 'b', 'c']
        assert exp_obj.final.kernel6.t02.tokens == ['g', 'h', 'i']
        assert exp_obj.final.kernel8.topics == ['t00', 't01', 't02']
        assert exp_obj.final.top10.t02.tokens == ['z', 'a1', 'b1']
        assert exp_obj.final.top100.t00.tokens == ['c1', 'd1', 'e1']
        assert exp_obj.final.top100.t01.tokens == ['f1', 'g1', 'h1']
        assert len(exp_obj.final.top100.t02) == 3
        assert 'j1' in exp_obj.final.top100.t02
        assert exp_obj.final.top_defs == ['top-tokens-10', 'top-tokens-100']
        assert exp_obj.final.kernels == ['kernel60', 'kernel80']
        assert exp_obj.final.background_tokens == ['l1', 'm1', 'n1']

        assert exp_obj.tracked.background_tokens_ratio_3.all ==  [0.4, 0.3, 0.2]
        assert exp_obj.tracked.background_tokens_ratio_3.last == 0.2
