workspace "RoadAnomaly" "Pixel-level road anomaly detection: current contracts and planned offline pipeline." {

    model {
        researcher = person "Researcher / ML engineer" "Configures runs, trains candidates and records evidence." "Element,Person"
        evaluator = person "Evaluator / reviewer" "Reviews selection evidence, held-out scores and explanations." "Element,Person"

        roadAnomaly = softwareSystem "RoadAnomaly" "Repository and planned offline anomaly-scoring pipeline. The dataset and contract tests are implemented; models, metrics and XAI are planned." "Element,Project" {
            benchmarkDataset = container "RoadAnomaly benchmark" "60 tracked frames, semantic masks, instances and credits. Evaluation-only." "Tracked data" "Element,Implemented,Data"
            contractTests = container "Contract tests" "Dataset integrity and architecture/documentation guardrails." "pytest + Structurizr validation" "Element,Implemented"
            experimentLog = container "Experiment records" "Run records and templates. The template/index exist; no experiment has run." "Markdown" "Element,Template,Data"

            normalRoadManifest = container "Normal-road manifest" "Pinned release, class map, label hashes and scene-grouped split hash." "YAML + image/label files" "Element,Planned,Data"
            dataPipeline = container "Data pipeline" "Decode, resize, augment and scene-grouped tf.data batches." "Python / TensorFlow" "Element,Planned"
            training = container "Training" "Autoencoder, U-Net and DeepLabV3+ training on normal-road data." "TensorFlow / Keras" "Element,Planned"
            modelArtifacts = container "Model artifacts" "Checkpoints and exported SavedModels with preprocessing manifests." "Filesystem" "Element,Planned,Data"
            normalRoadValidation = container "Normal-road validation" "Scene-grouped validation and native model diagnostics." "Python" "Element,Planned"
            selectionScorecard = container "Selection scorecard" "Documented multi-criteria selection; no RoadAnomaly number." "Markdown / JSON" "Element,Planned,Guardrail"
            benchmarkEvaluation = container "RoadAnomaly evaluation" "Common binary-mask metrics on all 60 held-out frames. Report-only." "Python" "Element,Planned"
            xai = container "XAI evidence" "Reconstruction-error maps, Seg-Grad-CAM, Integrated Gradients and faithfulness checks." "Python" "Element,Planned"
            registry = container "Model registry" "All three candidate SavedModels and manifests, plus the selected alias." "OCI / filesystem" "Element,Planned,Data"
        }

        normalRoadCorpora = softwareSystem "Normal-road corpora" "Cityscapes / BDD100K normal-road subsets, labels and licences. Not yet pinned." "Element,ExternalPlanned"
        pretrainedWeights = softwareSystem "Pretrained weights" "ImageNet / pretrained encoder weights used to initialise segmentation models." "Element,ExternalPlanned"
        githubActions = softwareSystem "GitHub Actions" "CI quality gate, gated delivery jobs and immutable artifact publication." "Element,ExternalImplemented"

        researcher -> training "configures and runs"
        evaluator -> experimentLog "reviews evidence"

        githubActions -> contractTests "runs lint, types, contract tests and delivery gates"

        normalRoadCorpora -> normalRoadManifest "source release, labels and licence"
        normalRoadManifest -> dataPipeline "pinned scene-grouped splits"
        dataPipeline -> training "normal-road batches"
        pretrainedWeights -> training "initialises encoders"
        training -> modelArtifacts "saves best checkpoints"

        modelArtifacts -> normalRoadValidation "loads candidate models"
        normalRoadValidation -> selectionScorecard "native metrics and uncertainty"
        selectionScorecard -> registry "selects alias; retains all three"
        selectionScorecard -> experimentLog "writes selection rationale"

        modelArtifacts -> benchmarkEvaluation "loads candidate models"
        benchmarkDataset -> benchmarkEvaluation "scores all 60 frames"
        benchmarkEvaluation -> experimentLog "writes report-only metrics"

        registry -> xai "selected model and immutable digest"
        xai -> experimentLog "writes explanations and faithfulness checks"
    }

    views {
        systemContext roadAnomaly "c1-system-context" "Target system context" {
            include *
            autoLayout tb
        }

        container roadAnomaly "c2-offline-pipeline" "Target offline training and evaluation pipeline" {
            include *
            autoLayout tb
        }

        styles {
            element "Element" {
                background "#FFFFFF"
                color "#1F2937"
                fontSize 14
            }
            element "Person" {
                background "#E8EEF7"
                color "#1E3A5F"
                shape "Person"
            }
            element "Project" {
                background "#F8FAFC"
                color "#0F172A"
            }
            element "Implemented" {
                background "#DCEBE5"
                color "#123B35"
            }
            element "Planned" {
                background "#F6EBDD"
                color "#5C3D18"
            }
            element "Template" {
                background "#E8EEF7"
                color "#1E3A5F"
            }
            element "ExternalPlanned" {
                background "#E5E7EB"
                color "#374151"
            }
            element "ExternalImplemented" {
                background "#DCEBE5"
                color "#123B35"
            }
            element "Data" {
                shape "Cylinder"
            }
            element "Guardrail" {
                background "#EDE9FE"
                color "#4C1D95"
            }
            relationship "Relationship" {
                color "#6B7280"
                fontSize 14
            }
        }
    }
}
