import logging
import numpy as np

from typing import Dict, List

from webserver.tasks import task_keeper
from webserver.utilities.configuration import configuration

logger = logging.getLogger(__name__)

featureExtractor = None
la = None

if "protbert_annotations" in configuration['celery']['celery_worker_type']:
    from bio_embeddings.extract.basic.BasicAnnotationExtractor import BasicAnnotationExtractor
    from bio_embeddings.extract.light_attention import LightAttentionAnnotationExtractor

    from bio_embeddings.utilities import convert_list_of_enum_to_string

    logger.info("Loading the feature extraction models...")

    featureExtractor = BasicAnnotationExtractor(
        "bert_from_publication",
        secondary_structure_checkpoint_file=configuration['prottrans_bert_bfd']['secondary_structure_checkpoint_file'],
        subcellular_location_checkpoint_file=configuration['prottrans_bert_bfd']['subcellular_location_checkpoint_file']
    )

    la = LightAttentionAnnotationExtractor(
        membrane_checkpoint_file=configuration['prottrans_bert_bfd']['la_solubility_checkpoint_file'],
        subcellular_location_checkpoint_file=configuration['prottrans_bert_bfd']['la_subcellular_location_checkpoint_file']
    )

    logger.info("Finished initializing.")


@task_keeper.task()
def get_protbert_annotations_sync(embedding: List) -> Dict[str, str]:
    embedding = np.asarray(embedding)

    annotations = featureExtractor.get_annotations(embedding)
    la_annotations = la.get_subcellular_location(embedding)

    return {
        "predictedDSSP3": convert_list_of_enum_to_string(annotations.DSSP3),
        "predictedDSSP8": convert_list_of_enum_to_string(annotations.DSSP8),
        "predictedDisorder": convert_list_of_enum_to_string(annotations.disorder),
        "predictedMembrane": la_annotations.membrane.value,
        "predictedSubcellularLocalizations": la_annotations.localization.value,
        "predictedCCO": [],
        "predictedBPO": [],
        "predictedMFO": [],
        "meta": {
            "predictedDSSP3": "ProtBertSec, https://arxiv.org/pdf/2007.06225",
            "predictedDSSP8": "ProtBertSec, https://arxiv.org/pdf/2007.06225",
            "predictedDisorder": "ProtBertSec, https://arxiv.org/pdf/2007.06225",
            "predictedCCO": "unavailable",
            "predictedBPO": "unavailable",
            "predictedMFO": "unavailable",
            "predictedMembrane": "LA_ProtBert, https://www.biorxiv.org/content/10.1101/2021.04.25.441334v1",
            "predictedSubcellularLocalizations": "LA_ProtBert, https://www.biorxiv.org/content/10.1101/2021.04.25.441334v1",
        }
    }