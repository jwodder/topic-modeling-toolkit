import os
import sys
from configparser import ConfigParser
import pytest

from patm.build_coherence import CoherenceFilesBuilder
from patm.modeling.trainer import TrainerFactory
from patm.modeling import Experiment
from patm import Tuner
from patm.discreetization import PoliticalSpectrumManager
from patm.definitions import SCALE_PLACEMENT, DISCRETIZATION


from processors import Pipeline, PipeHandler
from reporting import ResultsHandler


MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(MODULE_DIR, 'data')

TEST_PIPELINE_CFG = os.path.join(MODULE_DIR, 'test-pipeline.cfg')
TRAIN_CFG = os.path.join(MODULE_DIR, 'test-train.cfg')
REGS_CFG = os.path.join(MODULE_DIR, 'test-regularizers.cfg')


TEST_COLLECTIONS_ROOT_DIR_NAME = 'unittests-collections'

TEST_COLLECTION = 'unittest-dataset'
MODEL_1_LABEL = 'test-model-1'


@pytest.fixture(scope='session')
def collections_root_dir(tmpdir_factory):
    return str(tmpdir_factory.mktemp(TEST_COLLECTIONS_ROOT_DIR_NAME))

@pytest.fixture(scope='session')
def test_collection_name():
    return TEST_COLLECTION

#
@pytest.fixture(scope='session')
def rq1_cplsa_results_json():
    """These are the results gathered for a cplsa trained model"""
    return os.path.join(DATA_DIR, 'cplsa100000_0.2_0.json')


@pytest.fixture(scope='session')
def test_collection_dir(collections_root_dir, test_collection_name, tmpdir_factory):
    if not os.path.isdir(os.path.join(collections_root_dir, test_collection_name)):
        os.mkdir(os.path.join(collections_root_dir, test_collection_name))
    return os.path.join(collections_root_dir, test_collection_name)
    # return str(tmpdir_factory.mktemp(os.path.join(collections_root_dir, test_collection_name)))
    # return os.path.join(collections_root_dir, TEST_COLLECTION)

@pytest.fixture(scope='session')
def results_handler(collections_root_dir):
    return ResultsHandler(collections_root_dir, results_dir_name='results')

@pytest.fixture(scope='session', params=[[100, 100]])
def sample_n_real(request):
    return request.param

@pytest.fixture(scope='session')
def pairs_file_nb_lines():  # number of lines in cooc and ppmi files (771 in python2, 759 in python3)
    python3 = {True: 759,  # Dirty code to support python 2 backwards compatibility
               False: 771}
    return python3[2 < sys.version_info[0]]

@pytest.fixture(scope='session')
def pipe_n_quantities(sample_n_real, pairs_file_nb_lines):
    return [TEST_PIPELINE_CFG] + sample_n_real + [1297,
                                                  833,
                                                  834,
                                                  pairs_file_nb_lines]



@pytest.fixture(scope='session')
def test_dataset(test_collection_dir, pipe_n_quantities):
    """A dataset ready to be used for topic modeling training. Depends on the input document sample size to take and resulting actual size"""
    sample = pipe_n_quantities[1]
    pipeline_cfg = pipe_n_quantities[0]
    pipe_handler = PipeHandler()
    # pipe_handler.pipeline = Pipeline.from_cfg(pipe_n_quantities[0])
    psm = PoliticalSpectrumManager(SCALE_PLACEMENT, DISCRETIZATION)
    text_dataset = pipe_handler.preprocess('posts', pipeline_cfg, test_collection_dir, psm.poster_id2ideology_label, psm.class_names, sample=sample, add_class_labels_to_vocab=True)
    coh_builder = CoherenceFilesBuilder(test_collection_dir)
    coh_builder.create_files(cooc_window=10, min_tf=0, min_df=0, apply_zero_index=False)
    return text_dataset

# PARSE UNITTEST CFG FILES

def parse_cfg(cfg):
    config = ConfigParser()
    config.read(cfg)
    return {section: dict(config.items(section)) for section in config.sections()}


@pytest.fixture(scope='session')
def train_settings():
    """These settings (learning, reg components, score components, etc) are used to train the model in 'trained_model' fixture. A dictionary of cfg sections mapping to dictionaries with settings names-values pairs."""
    _ = parse_cfg(TRAIN_CFG)
    _['regularizers'] = {k: v for k, v in _['regularizers'].items() if v}
    _['scores'] = {k: v for k, v in _['scores'].items() if v}
    return _


# @pytest.fixture(scope='session')
# def reg_settings():
#     """These regularizers' initialization (eg tau coefficient value/trajectory) settings are used to train the model in 'trained_model' fixture. A dictionary of cfg sections mapping to dictionaries with settings names-values pairs."""
#     return parse_cfg(REGS_CFG)


@pytest.fixture(scope='session')
def trainer(collections_root_dir, test_dataset):
    return TrainerFactory().create_trainer(os.path.join(collections_root_dir, test_dataset.name), exploit_ideology_labels=True, force_new_batches=True)

#
# @pytest.fixture(scope='session')
# def cooc_dicts(trainer):
#     return trainer.cooc_dicts



# @pytest.fixture(scope='session')
# def trainer_n_experiment(test_dataset, collections_root_dir):
#     trainer = TrainerFactory(collections_root_dir=collections_root_dir).create_trainer(test_dataset.name, exploit_ideology_labels=True, force_new_batches=True)
#     experiment = Experiment(os.path.join(collections_root_dir, test_dataset.name), trainer.cooc_dicts)
#     trainer.register(experiment)  # when the model_trainer trains, the experiment object keeps track of evaluation metrics
#     return trainer, experiment


@pytest.fixture(scope='session')
def trained_model_n_experiment(collections_root_dir, test_dataset, trainer):
    experiment = Experiment(os.path.join(collections_root_dir, test_dataset.name), trainer.cooc_dicts)
    topic_model = trainer.model_factory.create_model(MODEL_1_LABEL, TRAIN_CFG, reg_cfg=REGS_CFG, show_progress_bars=False)
    train_specs = trainer.model_factory.create_train_specs()
    trainer.register(experiment)
    experiment.init_empty_trackables(topic_model)
    trainer.train(topic_model, train_specs, effects=False, cache_theta=True)
    return topic_model, experiment


@pytest.fixture(scope='session')
def loaded_model_n_experiment(collections_root_dir, test_dataset, trainer, trained_model_n_experiment):
    model, experiment = trained_model_n_experiment
    experiment.save_experiment(save_phi=True)
    new_exp_obj = Experiment(os.path.join(collections_root_dir, test_dataset.name), trainer.cooc_dicts)
    trainer.register(new_exp_obj)
    loaded_model = new_exp_obj.load_experiment(model.label)
    return loaded_model, new_exp_obj


    # if args.load:
    #     topic_model = experiment.load_experiment(args.label)
    #     print '\nLoaded experiment and model state'
    #     settings = cfg2model_settings(args.config)
    #     train_specs = TrainSpecs(15, [], [])




@pytest.fixture(scope='session')
def tuner_obj(collections_root_dir, test_dataset):
    from patm.tuning.building import tuner_definition_builder as tdb
    tuner = Tuner(os.path.join(collections_root_dir, test_dataset.name), evaluation_definitions={
        'perplexity': 'per',
        'sparsity-phi-@dc': 'sppd',
        'sparsity-theta': 'spt',
        'topic-kernel-0.60': 'tk60',
        'topic-kernel-0.80': 'tk80',
        'top-tokens-10': 'top10',
        'top-tokens-100': 'top100',
        'background-tokens-ratio-0.3': 'btr3',
        'background-tokens-ratio-0.2': 'btr2'
    }, verbose=0)

    tuning_definition = tdb.initialize()\
        .nb_topics(10, 12)\
        .collection_passes(5)\
        .document_passes(1)\
        .background_topics_pct(0.2) \
        .ideology_class_weight(0, 1) \
        .build()

        # .sparse_phi()\
        #     .deactivate(8)\
        #     .kind('linear')\
        #     .start(-1)\
        #     .end(-10, -100)\
        # .sparse_theta()\
        #     .deactivate(10)\
        #     .kind('linear')\
        #     .start(-1)\
        #     .end(-10, -100)\

    tuner.active_regularizers = [
        # 'smooth-phi',
        # 'smooth-theta',
        'label-regularization-phi-dom-cls',
        'decorrelate-phi-dom-def',
    ]
    tuner.tune(tuning_definition,
               prefix_label='unittest',
               append_explorables=True,
               append_static=True,
               force_overwrite=True,
               verbose=False)
    return tuner