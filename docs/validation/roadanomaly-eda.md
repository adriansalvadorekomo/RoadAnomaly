Source JSON SHA-256: `46e50e8ce998139f5ce1b096df79dfd820fe0034e3faea1a7f73a756f14acec2` (`computed_local`)

## 1. Scope and method

This audit covers only the 60 held-out RoadAnomaly benchmark frames and is read-only over `data/` (`computed_local`). The benchmark is evaluation-only: no model was fitted, selected, tuned, scored or promoted (`documented_local`).

Evidence classes are visible on every quantitative, provenance and licensing statement: `computed_local`, `documented_local`, `upstream_unverified` or `unresolved`. Visual registration, overlays, aggregate figures, the review ledger and normal-road readiness are post-MVP extensions and are not assessed here (`unresolved`).

## 2. Environment and reproduction

| Item | Value | Evidence |
|---|---|---|
| Source commit | b4d40dce5d4a1f44e4586174b41cb9ad79c6077f | computed_local |
| Python | 3.12.13 | computed_local |
| NumPy | 2.5.4 | computed_local |
| Pillow | 13.0.0 | computed_local |
| jsonschema | 4.26.0 | computed_local |
| Audit version | 1.0 | computed_local |
| Canonical command | make data-audit | computed_local |
| Check command | make data-audit-check | documented_local |

`environment.commit` is recorded provenance, not a revalidated git ancestry claim (`upstream_unverified`). Matplotlib and figure versions are not claimed or required (`unresolved`).

## 3. Fingerprint

Recipe (`documented_local`): `regular files under data/ (no symlinks), sorted by POSIX relative path; for each: UTF-8 path + NUL + raw 32-byte SHA-256 of content; no trailing NUL/newline; lowercase hex`.

| Property | Value | Evidence |
|---|---|---|
| Historical value | `7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2` | computed_local |
| Historical counts | 677 files, 13135474 bytes | computed_local |
| Computed value | `7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2` | computed_local |
| Current counts | 677 files, 13135474 bytes | computed_local |
| Status | match | computed_local |
| Provenance | local_reconstruction | upstream_unverified |

The historical recipe is a local reconstruction. Matching it does not prove the original Stage 2 implementation byte layout (`upstream_unverified`). Current counts do not replace the historical baseline (`computed_local`).

## 4. Inventory and integrity

| Property | Value | Evidence |
|---|---|---|
| Frame-list entries | 60 | computed_local |
| Frames on disk | 60 | computed_local |
| Label directories | 60 | computed_local |
| Instance-annotated frames | 46 | computed_local |
| Semantic-only frames | 14 | computed_local |
| Image size | 1280 x 720 | computed_local |
| Image mode | RGB | computed_local |

| Integrity check | Value | Evidence |
|---|---|---|
| Semantic values | [0, 2] | computed_local |
| Colour mapping | {'anomaly': [255, 69, 0], 'normal': [0, 0, 0]} | computed_local |
| Colour mapping valid | true | computed_local |
| Instance class ID | 2 | computed_local |
| Contiguous instance IDs | true | computed_local |
| Label files complete | true | computed_local |
| Frame decodable | true | computed_local |

| Frame | Annotation | Size | Mode | Frame SHA-256 | Evidence |
|---|---|---|---|---|---|
| animals01_Guiguinto_railway_station_Calves.webp | instance | 1280 x 720 | RGB | `7cbd648e21a5cc0c2b5806138a3307db06090e112cd6f61547bbf4e915cca857` | computed_local |
| animals02_Zagori_On_the_road_to_Papigko.webp | instance | 1280 x 720 | RGB | `d09cb33f33fb55fb4f0571fe08387f2953fb58eb066c9ba004d934fd68eb6b3b` | computed_local |
| animals03_Zebras_in_the_road.webp | instance | 1280 x 720 | RGB | `a44205f8e9a4b0c7ecc50888832e0c63d5e23372bb13b8a9984d1163bf200801` | computed_local |
| animals04_17_animal_casualties_so_far_in_2006.webp | instance | 1280 x 720 | RGB | `c072e047007a050ae46abf0caa7be45b6e0229abe0846a82340ff059e4b310fe` | computed_local |
| animals05_cows_near_Phonsavan_Laos.webp | instance | 1280 x 720 | RGB | `e926ffc81117cdb43d3c82c7cc68c99963d1207e2b2ebdac77fd7301e07eed9f` | computed_local |
| animals06_sheep_roads_lambs.webp | semantic_only | 1280 x 720 | RGB | `07790ab94e62593ecb298a91d3d31f4e68a7c31f266b630a56169ce325ba28ef` | computed_local |
| animals07_Aihole_Pattadakal.webp | instance | 1280 x 720 | RGB | `53357667478c0075c40094311c1f5340fdbd0b6c90d12b6b96abb16110ad97d9` | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | instance | 1280 x 720 | RGB | `2569e591efc723dd9e780f6b60b80b9f8b3edb82f8d702b2b703cc4be0283e0d` | computed_local |
| animals09_working_together.webp | semantic_only | 1280 x 720 | RGB | `cd0da295fe3f07b9329e63a934f755fb79df47ef53d8eaddd86b422179780053` | computed_local |
| animals10_bovine_cattle_beside_road.webp | instance | 1280 x 720 | RGB | `c45f36191127fc1b83620e551367c69095f5020eb3b98a32ccdff50fb63d76a9` | computed_local |
| animals11_Cock_Pheasant_on_Romford_Road.webp | instance | 1280 x 720 | RGB | `833824f4820dee57977ea46b3331ba81e10c8775221514e9b755fbe6c86d6f78` | computed_local |
| animals12_Collared_Peccary_crossing_the_road.webp | instance | 1280 x 720 | RGB | `eb158544b268942ad8b5d62aea423e701b264638c2a66e58cb57619bd132c023` | computed_local |
| animals13_jeune_bovin_sur_la_route.webp | instance | 1280 x 720 | RGB | `57a289b7647d0392d4c259218594af7683de6cb89ffbda842407165b66b5efb8` | computed_local |
| animals14_Dekemhare_Road.webp | instance | 1280 x 720 | RGB | `c8c97ae60ca5edbc460026b9a4ab405db23f6e30ac41dd0aaf0ff6cb01eb192d` | computed_local |
| animals15_Doebeln_Pferdebahn.webp | instance | 1280 x 720 | RGB | `a170f8c9af21390d7940cac6f08299b865418e382fdb6d86287ec24d678b4a32` | computed_local |
| animals16_Donkeys_of_Morocco.webp | instance | 1280 x 720 | RGB | `a4bcf9739a3a4731c99ba7c4bd6def97300eb8a9f61932c7656570422c34365c` | computed_local |
| animals17_E6_near_Kvaenangen.webp | instance | 1280 x 720 | RGB | `9a120e7b9dee32f14ad1c16d05e5daef56a6c617c13a88a053f4a6b1ae9963dd` | computed_local |
| animals18_Goose_on_the_road_Memphis.webp | instance | 1280 x 720 | RGB | `db7c6bc15e41548dfb952e618a55990e52523dfe45a639214f164c5312fd95b0` | computed_local |
| animals19_Porte_de_Roubaix.webp | instance | 1280 x 720 | RGB | `f425f2431ae74020a9c67c983949151c19e5d98d7fc4c220c62fcab7cd95e535` | computed_local |
| animals20_Marcassin_Conchiglio.webp | instance | 1280 x 720 | RGB | `d26bb8e944c5493290e600576b5b7684f177fd6f3d94ae0ee3cbbbf49b65fd95` | computed_local |
| animals21_On_The_Road_to_Gondar_Ethiopia.webp | semantic_only | 1280 x 720 | RGB | `a219214c17e506abd3031acf2fbe46e25fc4d4f3a4c120bc79e0da68309c82cd` | computed_local |
| animals22_red_fox_on_road.webp | instance | 1280 x 720 | RGB | `9b39a76aa4151a4588ae5cf9b31b07c1b988f645d060d651b144a82d3b80fb86` | computed_local |
| animals23_rhino_crossing_road.webp | instance | 1280 x 720 | RGB | `c5093c8ae635b883672225716ea6fe4fb2ad88704e4ab9607978dad37a81cdab` | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | instance | 1280 x 720 | RGB | `df5b618bfcfdc746f13f7199b604b2e8fd578c7769835485515c719a7aebefe9` | computed_local |
| animals25_jablonna_dziki.webp | semantic_only | 1280 x 720 | RGB | `dd5572ea5587f703120367b23dc8492ec0f962997e14c760a070576308f20f0d` | computed_local |
| animals26_Unnamed_Road_Kazakhstan.webp | instance | 1280 x 720 | RGB | `77b3fd82b24e7739717fbcc5d12cb3fe6b1303b234254ef438e42baa203cbff8` | computed_local |
| animals27_wildlife_bear.webp | instance | 1280 x 720 | RGB | `bad60141bc09b861f8234f7074979507bca4f5179d289ef85f781a47f7353a06` | computed_local |
| animals28.webp | instance | 1280 x 720 | RGB | `da51b37091a26f1e7d500e250220c13ebdef87faf7bf560d82aa7e5ef0e25c23` | computed_local |
| animals29_Zebra_Crossing_Abbey_Road_Style.webp | instance | 1280 x 720 | RGB | `5144eb8b8772d41f5fbbb39168734229aa75e25c0053cd3fdab7ec6a14e56d33` | computed_local |
| animals30.webp | instance | 1280 x 720 | RGB | `2e0e8bf8e84b8a3ffda58c4dcc309c9c85977b0356fcc69b552618f57c9d8c68` | computed_local |
| animals31_deer.webp | semantic_only | 1280 x 720 | RGB | `ea381d9b87e5d2d8be17c6c7605e119a0819e0f25383370a3193c45de6027d6a` | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | instance | 1280 x 720 | RGB | `c65f9a5d4eef1522525b3b29c7ba3a31e2b404f0e934b3f5cc80738d83654666` | computed_local |
| cones02_Broadmoor_Manhole_Cones.webp | instance | 1280 x 720 | RGB | `a992469683528e97a62c02b22f4c9ea732b0d3f118dcc0cd185e7bbb06ec3e90` | computed_local |
| cones03_Bang_Na_Trat_Highway.webp | instance | 1280 x 720 | RGB | `794a567fbaaf93c333e8bc7950aea07000028b564f6cea468207c8b8552b9361` | computed_local |
| cones04_Federation.webp | instance | 1280 x 720 | RGB | `e8873bc07583758e0c5c0cbba65ed2d889725a9112878c3c520939847a717596` | computed_local |
| cones05_Corner_of_Kingsley_Park.webp | instance | 1280 x 720 | RGB | `55ee13fde79daecdb4cd09f5838035ceaba8601f793ff97636b2702f41338c22` | computed_local |
| cones06_VnA_traffic_cones.webp | instance | 1280 x 720 | RGB | `3bac3d7a7c06fde88344b9c86f33ab0f2fffb11af46c850e27983f0b52f03351` | computed_local |
| cones07.webp | semantic_only | 1280 x 720 | RGB | `6314acf5105c2625982b959b6c0028bd42d0ce6fbbb97888323210916c6aab78` | computed_local |
| cones08_can.webp | semantic_only | 1280 x 720 | RGB | `f3a08b600ed12f3dd53510917ed0c4c635cd8c746f90e32c49e43c6788dca176` | computed_local |
| lost_tires03.webp | instance | 1280 x 720 | RGB | `911fe4730983a0a169e2c164f37067b7c0e8654bc2b59f9479fa318a722b5ae8` | computed_local |
| lost_tires08.webp | instance | 1280 x 720 | RGB | `1e3a7887c08bd8c00af2d94a0acc37a0bd04bada13cadf9905c74a32ba0d3977` | computed_local |
| lost_tires09.webp | instance | 1280 x 720 | RGB | `02045a0bade92e2ac7304b51e4e83dda72ad80941b8a1cb05ae1e014ee03eb48` | computed_local |
| obstacles01_boulder.webp | semantic_only | 1280 x 720 | RGB | `081c09ae6964c105b32ba55c542a881752f106db9a4679cf93f497ca85e7e5f0` | computed_local |
| obstacles02_rock.webp | semantic_only | 1280 x 720 | RGB | `1ad13eaad71b3e6bff0cea41827a14d55295aea760a13ee30d93ad2acf935047` | computed_local |
| obstacles03_cardboard_czech_hedgehog.webp | instance | 1280 x 720 | RGB | `0578198becadb6834efcf36d582eca8cbe935fd74f3add3904569859e84eaa74` | computed_local |
| obstacles04_cardboard_czech_hedgehog.webp | instance | 1280 x 720 | RGB | `0d7f860776a19974a0cc5a304bd8b0566e15a3bbf1067ce51c7e3516c6289130` | computed_local |
| obstacles05_cardboard_czech_hedgehog.webp | instance | 1280 x 720 | RGB | `705c9e13c6765ac0fa12e8672fc2850f33f71a1663357835f180963a817b0784` | computed_local |
| obstacles06_cardboard_czech_hedgehog.webp | instance | 1280 x 720 | RGB | `57de5577bc2b71cbe52f8c11f5cc6b42d37acac3b37c38a4b4f4bf8906471c6b` | computed_local |
| obstacles07_czech_hedgehog.webp | semantic_only | 1280 x 720 | RGB | `80e6263ca33a93b40c4dfbb072efb3ff48a88be8dd8242fab0ec591fa61a1619` | computed_local |
| obstacles08_boulder2.webp | semantic_only | 1280 x 720 | RGB | `052b2d469b2db45541f47fe942454073651afb6cfadc795bcf086a4e802db17d` | computed_local |
| obstacles09_boulder3.webp | semantic_only | 1280 x 720 | RGB | `9a77f167d84ca68903eeedba2c77daaf2e517a8e1417d96db9f8e56c83d63b56` | computed_local |
| obstacles10_boulder4.webp | semantic_only | 1280 x 720 | RGB | `e81b7c1dc00c5a0f38de34ed0f9241368a3f685c17362ef9b554d8417a129b12` | computed_local |
| obstacles11_boulder5.webp | semantic_only | 1280 x 720 | RGB | `5372217a1df8502d5ec579fb70ed5131342c266fabbf0be36ccfb0c40ff1a116` | computed_local |
| obstacles12_rocks2.webp | instance | 1280 x 720 | RGB | `c4df5122c16442d7c6881b23dab4331fd2331fbb79a6182451b479b814d6c626` | computed_local |
| obstacles12_rocks4.webp | instance | 1280 x 720 | RGB | `87f9c7a7d6f77ba382b20025d12bfcbc2f15794129539901823bcffaba6ab2c9` | computed_local |
| obstacles12_rocks5.webp | instance | 1280 x 720 | RGB | `6c33b9076e9e357787ab08f07edbee08d60629767d9a3e9651193de65cf66d9d` | computed_local |
| obstacles12_rocks6.webp | instance | 1280 x 720 | RGB | `e1bee81010b004085440d38f18af1d6bb8cc70c212b69c26e07d867aa6318be1` | computed_local |
| vehicle01_man_carrying_dry_grass_on_bicycle.webp | instance | 1280 x 720 | RGB | `3cddd7b3d7a338553e659c08192d0b5b6b7c234b632cfb83143a4e2b2ef55805` | computed_local |
| vehicle02_Broadmoor_Cones_Skidloader.webp | instance | 1280 x 720 | RGB | `1465eb68f1d43c64372ffdc02a13f49041088b213271b19d6e5ef2c8d8320eb1` | computed_local |
| vehicle03_Fuhrwerke_in_China.webp | instance | 1280 x 720 | RGB | `2062ded2b23cf19f85267f6bafb0ea91bfe881f8e5300f2cd8309e6e49f570fa` | computed_local |

## 5. Instance/semantic consistency

Definition (`documented_local`): `union(instance values 1..N) == semantic value 2, per instance frame`.

| Property | Value | Evidence |
|---|---|---|
| Frames checked | 46 | computed_local |
| Frames exact | 46 | computed_local |
| Frames mismatched | 0 | computed_local |
| Extra instance pixels | 0 | computed_local |
| Missing instance pixels | 0 | computed_local |
| Semantic-only frames excluded | 14 | computed_local |

A mismatch is a hard exit-2 failure and is never serialized as this success shape (`computed_local`).

## 6. Coverage, categories and object scale

| Coverage property | Value | Evidence |
|---|---|---|
| Total anomaly pixels | 5446413 | computed_local |
| Total pixels | 55296000 | computed_local |
| Pooled fraction | 0.09849561 | computed_local |
| Pooled percent | 9.849561 | computed_local |
| Minimum per-frame percent | 0.374674 | computed_local |
| Maximum per-frame percent | 42.328559 | computed_local |
| Median per-frame percent | 6.622938 | computed_local |
| Frames below 1 percent | animals02_Zagori_On_the_road_to_Papigko.webp, animals11_Cock_Pheasant_on_Romford_Road.webp, lost_tires03.webp, lost_tires08.webp, lost_tires09.webp, obstacles12_rocks2.webp | computed_local |

Definitions (`documented_local`): `below_one_percent` = per-frame percent < 1.0; `median` = median of the 60 per-frame fractions; `per_frame_fraction` = anomaly pixels / (1280 x 720); `percent` = 100 x fraction; `pooled_fraction` = total anomaly pixels / total pixels over all 60 frames.

| Frame | Anomaly pixels | Fraction | Percent | Evidence |
|---|---|---|---|---|
| animals01_Guiguinto_railway_station_Calves.webp | 61817 | 0.06707574 | 6.707574 | computed_local |
| animals02_Zagori_On_the_road_to_Papigko.webp | 7365 | 0.00799154 | 0.799154 | computed_local |
| animals03_Zebras_in_the_road.webp | 215418 | 0.23374349 | 23.374349 | computed_local |
| animals04_17_animal_casualties_so_far_in_2006.webp | 60845 | 0.06602105 | 6.602105 | computed_local |
| animals05_cows_near_Phonsavan_Laos.webp | 134647 | 0.14610135 | 14.610135 | computed_local |
| animals06_sheep_roads_lambs.webp | 339571 | 0.36845812 | 36.845812 | computed_local |
| animals07_Aihole_Pattadakal.webp | 75530 | 0.08195530 | 8.195530 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 16251 | 0.01763346 | 1.763346 | computed_local |
| animals09_working_together.webp | 390100 | 0.42328559 | 42.328559 | computed_local |
| animals10_bovine_cattle_beside_road.webp | 25557 | 0.02773112 | 2.773112 | computed_local |
| animals11_Cock_Pheasant_on_Romford_Road.webp | 8521 | 0.00924588 | 0.924588 | computed_local |
| animals12_Collared_Peccary_crossing_the_road.webp | 120061 | 0.13027452 | 13.027452 | computed_local |
| animals13_jeune_bovin_sur_la_route.webp | 14547 | 0.01578451 | 1.578451 | computed_local |
| animals14_Dekemhare_Road.webp | 91804 | 0.09961372 | 9.961372 | computed_local |
| animals15_Doebeln_Pferdebahn.webp | 95684 | 0.10382378 | 10.382378 | computed_local |
| animals16_Donkeys_of_Morocco.webp | 287315 | 0.31175673 | 31.175673 | computed_local |
| animals17_E6_near_Kvaenangen.webp | 14962 | 0.01623481 | 1.623481 | computed_local |
| animals18_Goose_on_the_road_Memphis.webp | 11992 | 0.01301215 | 1.301215 | computed_local |
| animals19_Porte_de_Roubaix.webp | 86870 | 0.09425998 | 9.425998 | computed_local |
| animals20_Marcassin_Conchiglio.webp | 39840 | 0.04322917 | 4.322917 | computed_local |
| animals21_On_The_Road_to_Gondar_Ethiopia.webp | 140272 | 0.15220486 | 15.220486 | computed_local |
| animals22_red_fox_on_road.webp | 183445 | 0.19905056 | 19.905056 | computed_local |
| animals23_rhino_crossing_road.webp | 269268 | 0.29217448 | 29.217448 | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | 338376 | 0.36716146 | 36.716146 | computed_local |
| animals25_jablonna_dziki.webp | 124640 | 0.13524306 | 13.524306 | computed_local |
| animals26_Unnamed_Road_Kazakhstan.webp | 45283 | 0.04913520 | 4.913520 | computed_local |
| animals27_wildlife_bear.webp | 167615 | 0.18187391 | 18.187391 | computed_local |
| animals28.webp | 73954 | 0.08024523 | 8.024523 | computed_local |
| animals29_Zebra_Crossing_Abbey_Road_Style.webp | 64771 | 0.07028103 | 7.028103 | computed_local |
| animals30.webp | 61229 | 0.06643772 | 6.643772 | computed_local |
| animals31_deer.webp | 52627 | 0.05710395 | 5.710395 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 39294 | 0.04263672 | 4.263672 | computed_local |
| cones02_Broadmoor_Manhole_Cones.webp | 60484 | 0.06562934 | 6.562934 | computed_local |
| cones03_Bang_Na_Trat_Highway.webp | 13143 | 0.01426107 | 1.426107 | computed_local |
| cones04_Federation.webp | 12095 | 0.01312391 | 1.312391 | computed_local |
| cones05_Corner_of_Kingsley_Park.webp | 10107 | 0.01096680 | 1.096680 | computed_local |
| cones06_VnA_traffic_cones.webp | 46026 | 0.04994141 | 4.994141 | computed_local |
| cones07.webp | 12623 | 0.01369683 | 1.369683 | computed_local |
| cones08_can.webp | 18610 | 0.02019314 | 2.019314 | computed_local |
| lost_tires03.webp | 6407 | 0.00695204 | 0.695204 | computed_local |
| lost_tires08.webp | 3453 | 0.00374674 | 0.374674 | computed_local |
| lost_tires09.webp | 9148 | 0.00992622 | 0.992622 | computed_local |
| obstacles01_boulder.webp | 151657 | 0.16455838 | 16.455838 | computed_local |
| obstacles02_rock.webp | 151619 | 0.16451714 | 16.451714 | computed_local |
| obstacles03_cardboard_czech_hedgehog.webp | 68215 | 0.07401801 | 7.401801 | computed_local |
| obstacles04_cardboard_czech_hedgehog.webp | 43803 | 0.04752930 | 4.752930 | computed_local |
| obstacles05_cardboard_czech_hedgehog.webp | 68258 | 0.07406467 | 7.406467 | computed_local |
| obstacles06_cardboard_czech_hedgehog.webp | 42832 | 0.04647569 | 4.647569 | computed_local |
| obstacles07_czech_hedgehog.webp | 227478 | 0.24682943 | 24.682943 | computed_local |
| obstacles08_boulder2.webp | 12461 | 0.01352105 | 1.352105 | computed_local |
| obstacles09_boulder3.webp | 47374 | 0.05140408 | 5.140408 | computed_local |
| obstacles10_boulder4.webp | 175584 | 0.19052083 | 19.052083 | computed_local |
| obstacles11_boulder5.webp | 209403 | 0.22721680 | 22.721680 | computed_local |
| obstacles12_rocks2.webp | 5788 | 0.00628038 | 0.628038 | computed_local |
| obstacles12_rocks4.webp | 58159 | 0.06310655 | 6.310655 | computed_local |
| obstacles12_rocks5.webp | 16721 | 0.01814345 | 1.814345 | computed_local |
| obstacles12_rocks6.webp | 33442 | 0.03628689 | 3.628689 | computed_local |
| vehicle01_man_carrying_dry_grass_on_bicycle.webp | 119369 | 0.12952365 | 12.952365 | computed_local |
| vehicle02_Broadmoor_Cones_Skidloader.webp | 91892 | 0.09970920 | 9.970920 | computed_local |
| vehicle03_Fuhrwerke_in_China.webp | 70791 | 0.07681315 | 7.681315 | computed_local |

| Object category | Frames | Evidence |
|---|---|---|
| animals | 31 | computed_local |
| cones | 8 | computed_local |
| lost_tires | 3 | computed_local |
| obstacles | 15 | computed_local |
| vehicle | 3 | computed_local |

Classification (`computed_local`): `object_category_not_scene`. Filename prefixes are object categories, not scene IDs or split units.

| Object-scale property | Value | Evidence |
|---|---|---|
| ROI area below 1024 | 35 | computed_local |
| Both dimensions below 32 | 20 | computed_local |
| Either dimension below 32 | 46 | computed_local |
| Median ROI equivalent square (px) | 86.7 | computed_local |
| Median ROI width (px) | 85.0 | computed_local |
| Median ROI height (px) | 107.0 | computed_local |
| Median mask equivalent square (px) | 51.2 | computed_local |
| Denominator | 201 | computed_local |

Definitions (`documented_local`): `both_dimensions_below_32` = width < 32 and height < 32; `either_dimension_below_32` = width < 32 or height < 32; `mask_equivalent_square` = sqrt(count of nonzero instance-mask pixels); `roi_area` = (x1 - x0) x (y1 - y0), half-open extents; `roi_bounding_box` = median ROI width and height; `roi_equivalent_square` = sqrt(ROI area).

No single small-object definition is presented as the only truth (`computed_local`).

## 7. Instance mapping, ROI and duplicates

| Mapping property | Value | Evidence |
|---|---|---|
| Frames checked | 46 | computed_local |
| Frames agreeing | 35 | computed_local |
| Frames disagreeing | 11 | computed_local |
| Disagreeing frames | animals05_cows_near_Phonsavan_Laos.webp, animals08_on_the_main_street_of_village_Lin_Albania.webp, animals10_bovine_cattle_beside_road.webp, animals13_jeune_bovin_sur_la_route.webp, animals17_E6_near_Kvaenangen.webp, animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp, animals29_Zebra_Crossing_Abbey_Road_Style.webp, cones01_Beeston_MMB_A6_Middle_Street.webp, lost_tires09.webp, obstacles12_rocks6.webp, vehicle03_Fuhrwerke_in_China.webp | computed_local |
| Weaker existing test | max(mask) == len(instances) = True | computed_local |

The order mapping is `mask value k == instances[k-1].id`; it is not promoted above the weaker existing check (`computed_local`).

| Frame | Mask value | Index position | Index id | Evidence |
|---|---|---|---|---|
| animals05_cows_near_Phonsavan_Laos.webp | 4 | 4 | 5 | computed_local |
| animals05_cows_near_Phonsavan_Laos.webp | 5 | 5 | 6 | computed_local |
| animals05_cows_near_Phonsavan_Laos.webp | 6 | 6 | 8 | computed_local |
| animals05_cows_near_Phonsavan_Laos.webp | 7 | 7 | 9 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 1 | 1 | 2 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 2 | 2 | 3 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 3 | 3 | 4 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 4 | 4 | 6 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 5 | 5 | 7 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 6 | 6 | 8 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 7 | 7 | 9 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 8 | 8 | 10 | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | 9 | 9 | 11 | computed_local |
| animals10_bovine_cattle_beside_road.webp | 2 | 2 | 3 | computed_local |
| animals13_jeune_bovin_sur_la_route.webp | 2 | 2 | 16 | computed_local |
| animals13_jeune_bovin_sur_la_route.webp | 3 | 3 | 17 | computed_local |
| animals17_E6_near_Kvaenangen.webp | 1 | 1 | 2 | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | 5 | 5 | 6 | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | 6 | 6 | 7 | computed_local |
| animals29_Zebra_Crossing_Abbey_Road_Style.webp | 4 | 4 | 5 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 8 | 8 | 9 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 9 | 9 | 10 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 10 | 10 | 11 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 11 | 11 | 12 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 12 | 12 | 13 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 13 | 13 | 14 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 14 | 14 | 15 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 15 | 15 | 16 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 16 | 16 | 17 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 17 | 17 | 18 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 18 | 18 | 19 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 19 | 19 | 20 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 20 | 20 | 21 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 21 | 21 | 22 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 22 | 22 | 23 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 23 | 23 | 24 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 24 | 24 | 25 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 25 | 25 | 27 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 26 | 26 | 28 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 27 | 27 | 29 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 28 | 28 | 30 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 29 | 29 | 31 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 30 | 30 | 32 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 31 | 31 | 33 | computed_local |
| lost_tires09.webp | 1 | 1 | 2 | computed_local |
| obstacles12_rocks6.webp | 4 | 4 | 5 | computed_local |
| vehicle03_Fuhrwerke_in_China.webp | 3 | 3 | 4 | computed_local |
| vehicle03_Fuhrwerke_in_China.webp | 4 | 4 | 5 | computed_local |

| ROI property | Value | Evidence |
|---|---|---|
| Instances checked | 201 | computed_local |
| Out of bounds | 11 | computed_local |
| Non-tight | 17 | computed_local |
| Centroids inside | 201 | computed_local |

Definitions (`documented_local`): `centroid_containment` = 0 <= (bx0 + bx1) / 2 < 1280 and 0 <= (by0 + by1) / 2 < 720; `non_tight` = pixel box not strictly inside half-open ROI: bx0 < x0 or by0 < y0 or bx1 >= x1 or by1 >= y1; `out_of_bounds` = x0 < 0 or y0 < 0 or x1 > 1280 or y1 > 720, half-open extents.

| Out-of-bounds frame | Mask value | Evidence |
|---|---|---|
| animals07_Aihole_Pattadakal.webp | 2 | computed_local |
| animals14_Dekemhare_Road.webp | 6 | computed_local |
| animals14_Dekemhare_Road.webp | 8 | computed_local |
| animals16_Donkeys_of_Morocco.webp | 1 | computed_local |
| animals19_Porte_de_Roubaix.webp | 1 | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | 2 | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | 6 | computed_local |
| animals27_wildlife_bear.webp | 1 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 1 | computed_local |
| cones03_Bang_Na_Trat_Highway.webp | 1 | computed_local |
| obstacles12_rocks6.webp | 1 | computed_local |

| Non-tight frame | Mask value | Evidence |
|---|---|---|
| animals01_Guiguinto_railway_station_Calves.webp | 1 | computed_local |
| animals01_Guiguinto_railway_station_Calves.webp | 2 | computed_local |
| animals07_Aihole_Pattadakal.webp | 3 | computed_local |
| animals07_Aihole_Pattadakal.webp | 4 | computed_local |
| animals10_bovine_cattle_beside_road.webp | 1 | computed_local |
| animals14_Dekemhare_Road.webp | 4 | computed_local |
| animals16_Donkeys_of_Morocco.webp | 1 | computed_local |
| animals23_rhino_crossing_road.webp | 2 | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | 4 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 25 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 26 | computed_local |
| cones01_Beeston_MMB_A6_Middle_Street.webp | 30 | computed_local |
| cones03_Bang_Na_Trat_Highway.webp | 7 | computed_local |
| cones05_Corner_of_Kingsley_Park.webp | 6 | computed_local |
| obstacles12_rocks4.webp | 1 | computed_local |
| obstacles12_rocks4.webp | 4 | computed_local |
| obstacles12_rocks6.webp | 4 | computed_local |

ROIs and masks are reported without clipping or rewriting (`computed_local`).

Duplicate method (`documented_local`): `9x8 grayscale dHash, 64 bits; Hamming distance <= 6`.

| Duplicate method | Pairs | Evidence |
|---|---|---|
| Exact raw-file SHA-256 | [] | computed_local |
| Decoded RGB pixel buffer | [] | computed_local |
| dHash distance <= 6 | [] | computed_local |

- Limitation (`computed_local`): Exact file hashes detect byte-identical frames only.
- Limitation (`computed_local`): Decoded-pixel hashes detect identical RGB buffers after decoding, not near duplicates.
- Limitation (`computed_local`): The 9x8 grayscale dHash at Hamming distance <= 6 is method-limited; absence of reported pairs is not proof that no near-duplicate exists.
- Limitation (`computed_local`): No model-based perceptual duplicate check was performed.

## 8. Credits, licensing and provenance

| Credit property | Value | Evidence |
|---|---|---|
| Frames with credit entries | 60 | computed_local |
| Missing entries | [] | computed_local |
| Missing per-image licence tokens | animals25_jablonna_dziki.webp, animals28.webp, animals30.webp, animals31_deer.webp, cones07.webp, cones08_can.webp, lost_tires03.webp, lost_tires08.webp, lost_tires09.webp, obstacles01_boulder.webp, obstacles02_rock.webp, obstacles03_cardboard_czech_hedgehog.webp, obstacles04_cardboard_czech_hedgehog.webp, obstacles05_cardboard_czech_hedgehog.webp, obstacles06_cardboard_czech_hedgehog.webp, obstacles07_czech_hedgehog.webp, obstacles08_boulder2.webp, obstacles09_boulder3.webp, obstacles10_boulder4.webp, obstacles11_boulder5.webp, obstacles12_rocks2.webp, obstacles12_rocks4.webp, obstacles12_rocks5.webp, obstacles12_rocks6.webp | unresolved |
| Missing source URLs | obstacles12_rocks2.webp, obstacles12_rocks4.webp, obstacles12_rocks5.webp, obstacles12_rocks6.webp | unresolved |
| Source groups / frames | 4 / 13 | computed_local |

Missing per-image tokens remain `unresolved`, not evidence that an image is unlicensed (`unresolved`). Source groups are attribution-derived, not scene IDs (`computed_local`).

| Group | Source URL | Frames | Frame count | Evidence |
|---|---|---|---|---|
| source-group-001 | https://www.stuff.co.nz/auckland/local-news/papakura-courier/102189952/upsurge-in-traffic-turns-road-into-difficulttonegotiate-obstacle-course | cones07.webp, cones08_can.webp | 2 | computed_local |
| source-group-002 | https://www.youtube.com/watch?v=2ysuwejHZEg | lost_tires03.webp, lost_tires08.webp, lost_tires09.webp | 3 | computed_local |
| source-group-003 | https://jasondeansart.com/sculpture/moveable-barriers/ | obstacles03_cardboard_czech_hedgehog.webp, obstacles04_cardboard_czech_hedgehog.webp, obstacles05_cardboard_czech_hedgehog.webp, obstacles06_cardboard_czech_hedgehog.webp | 4 | computed_local |
| source-group-004 | null | obstacles12_rocks2.webp, obstacles12_rocks4.webp, obstacles12_rocks5.webp, obstacles12_rocks6.webp | 4 | computed_local |

| Frame | Licence tokens | Source URL | Attribution | Evidence |
|---|---|---|---|---|
| animals01_Guiguinto_railway_station_Calves.webp | CC0 | https://commons.wikimedia.org/wiki/File:03167JfGuiguinto_railway_station_Calves_grasslands_Tabe_Tuktukan_Calves_Roadsfvf_07.jpg | Florentino Floro, CC0 https://creativecommons.org/publicdomain/zero/1.0/deed.en | computed_local |
| animals02_Zagori_On_the_road_to_Papigko.webp | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Zagori_-_On_the_road_to_Papigko_-_panoramio.jpg | Numenor, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/deed.en | computed_local |
| animals03_Zebras_in_the_road.webp | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:Zebras_in_the_road_(2362228520).jpg | Chris Eason, CC BY 2.0 https://creativecommons.org/licenses/by/2.0/deed.en | computed_local |
| animals04_17_animal_casualties_so_far_in_2006.webp | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:17_animal_casualties_so_far_in_2006_-_geograph.org.uk_-_223415.jpg | Nigel Freeman, CC BY-SA 2.0 https://creativecommons.org/licenses/by-sa/2.0/deed.en | computed_local |
| animals05_cows_near_Phonsavan_Laos.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:20171116_Cows,_local_road_near_Phonsavan,_Laos_2938_DxO.jpg | Jakub Hałun, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| animals06_sheep_roads_lambs.webp | public domain | https://commons.wikimedia.org/wiki/File:Sheep_roads_lambs.jpg | Jon Sullivan, public domain | computed_local |
| animals07_Aihole_Pattadakal.webp | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Aihole-Pattadakal_road.JPG | Jonas Buchholz, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/deed.en | computed_local |
| animals08_on_the_main_street_of_village_Lin_Albania.webp | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:Animals_on_the_main_street_of_village_Lin,_Albania_(6851578103).jpg | S. Niebel / SuSanA, CC BY 2.0 https://creativecommons.org/licenses/by/2.0/deed.en | computed_local |
| animals09_working_together.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Animals_working_together.jpg | Gunjan Raj Giri, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| animals10_bovine_cattle_beside_road.webp | public domain | https://pixnio.com/fauna-animals/cows-and-calves/bovine-catle-beside-road | PIXNIO, public domain | computed_local |
| animals11_Cock_Pheasant_on_Romford_Road.webp | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:Cock_Pheasant_on_Romford_Road_-_geograph.org.uk_-_1816852.jpg | Oast House Archive, CC BY-SA 2.0 https://creativecommons.org/licenses/by-sa/2.0/ | computed_local |
| animals12_Collared_Peccary_crossing_the_road.webp | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:Collared_Peccary_crossing_the_road.jpg | Alan Vernon, CC BY 2.0 https://creativecommons.org/licenses/by/2.0/deed.en | computed_local |
| animals13_jeune_bovin_sur_la_route.webp | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:Corse_t%C3%AAt%C3%A9e_de_jeune_bovin_sur_la_route.jpg | febs https://www.flickr.com/people/febs, CC BY 2.0 https://creativecommons.org/licenses/by/2.0/deed.en | computed_local |
| animals14_Dekemhare_Road.webp | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:Dekemhare_Road_(8352533008).jpg | David Stanley, CC BY 2.0 https://creativecommons.org/licenses/by/2.0/deed.en | computed_local |
| animals15_Doebeln_Pferdebahn.webp | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:Doebeln-straba.jpg | Oxensepp, CC BY-SA 2.0 DE https://creativecommons.org/licenses/by-sa/2.0/de/deed.en | computed_local |
| animals16_Donkeys_of_Morocco.webp | CC BY 3.0 | https://commons.wikimedia.org/wiki/File:Donkeys_of_Morocco.JPG | Makary, CC BY 3.0 https://creativecommons.org/licenses/by/3.0/deed.en | computed_local |
| animals17_E6_near_Kvaenangen.webp | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:E6_near_Kv%C3%A6nangen.jpg | Arno van den Tillaart, CC BY-SA 2.0 https://creativecommons.org/licenses/by-sa/2.0/deed.en | computed_local |
| animals18_Goose_on_the_road_Memphis.webp | CC BY 3.0 | https://commons.wikimedia.org/wiki/File:Goose_on_the_road_Memphis_TN_2013-03-17_001.jpg | Thomas R Machnitzki (thomas@machnitzki.com), CC BY 3.0 https://creativecommons.org/licenses/by/3.0/deed.en | computed_local |
| animals19_Porte_de_Roubaix.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Lille_Et%C3%A92016_la_Porte_de_Roubaix_(1).jpg | Pierre André Leclercq, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| animals20_Marcassin_Conchiglio.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Marcassin_(animal)_%C3%A0_Conchiglio_(3).jpg | Gzen92, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| animals21_On_The_Road_to_Gondar_Ethiopia.webp | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:On_The_Road_to_Gondar,_Ethiopia_(2401865686).jpg | A. Davey, CC BY 2.0 https://creativecommons.org/licenses/by/2.0/deed.en | computed_local |
| animals22_red_fox_on_road.webp | public domain | https://commons.wikimedia.org/wiki/File:Red_fox_on_road.jpg | Laubenstein Ronald, public domain | computed_local |
| animals23_rhino_crossing_road.webp | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Rhino_crossing_road.JPG | Meganbeckett27, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/deed.en | computed_local |
| animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:Sheep_Herders_Block_the_Road_-_En_route_from_Kaleybar_to_Eskanlu_-_Iranian_Azerbaijan_-_Iran_(7421427006).jpg | Adam Jones, CC BY-SA 2.0 https://creativecommons.org/licenses/by-sa/2.0/deed.en | computed_local |
| animals25_jablonna_dziki.webp | none | https://www.legio24.pl/jablonna-rozdaja-preparat-odstraszajacy-dziki/ | Legio24.pl | unresolved |
| animals26_Unnamed_Road_Kazakhstan.webp | CC BY 3.0 | https://commons.wikimedia.org/wiki/File:Unnamed_Road,_070000,_Kazakhstan_-_panoramio_(8).jpg | Олег Ч, CC BY 3.0 https://creativecommons.org/licenses/by/3.0/deed.en | computed_local |
| animals27_wildlife_bear.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Wildlife43.jpg | Shreyanath, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| animals28.webp | none | http://nowodworski.info/uwaga-zwierzeta-na-drodze/ | Tygodnik Nowodworski | unresolved |
| animals29_Zebra_Crossing_Abbey_Road_Style.webp | CC BY 3.0 | https://commons.wikimedia.org/wiki/File:Zebra_Crossing_Abbey_Road_Style_(63894353).jpeg | Luca Canepa, CC BY 3.0 https://creativecommons.org/licenses/by/3.0/deed.en | computed_local |
| animals30.webp | none | https://moto.wp.pl/dzikie-zwierzeta-grozne-na-drodze-6068434518099073a | Wirtualna Polska | unresolved |
| animals31_deer.webp | none | https://driving-tests.org/beginner-drivers/how-to-avoid-obstacles-on-the-roadway/ | driving-tests.org | unresolved |
| cones01_Beeston_MMB_A6_Middle_Street.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Beeston_MMB_A6_Middle_Street.jpg | Mattbuck, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| cones02_Broadmoor_Manhole_Cones.webp | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:BroadmoorManholeConesJune2008.jpg | Infrogmation, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/deed.en | computed_local |
| cones03_Bang_Na_Trat_Highway.webp | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Emergency_traffic_control_on_Bang_Na_Trat_Highway_near_Chanthaburi.JPG | Khaosaming, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/deed.en | computed_local |
| cones04_Federation.webp | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Federation_chantier_aout_2006_-_5.JPG | Kyah117, CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0/deed.en | computed_local |
| cones05_Corner_of_Kingsley_Park.webp | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:Traffic_cones_on_the_corner_of_Kingsley_Park_-_geograph.org.uk_-_604201.jpg | Basher Eyre, CC BY-SA 2.0 https://creativecommons.org/licenses/by-sa/2.0/deed.en | computed_local |
| cones06_VnA_traffic_cones.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:V%26A_traffic_cones.jpg | HelenOnline, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| cones07.webp | none | https://www.stuff.co.nz/auckland/local-news/papakura-courier/102189952/upsurge-in-traffic-turns-road-into-difficulttonegotiate-obstacle-course | Imogen Neale stuff.co.nz | unresolved |
| cones08_can.webp | none | https://www.stuff.co.nz/auckland/local-news/papakura-courier/102189952/upsurge-in-traffic-turns-road-into-difficulttonegotiate-obstacle-course | Imogen Neale stuff.co.nz | unresolved |
| lost_tires03.webp | none | https://www.youtube.com/watch?v=2ysuwejHZEg | Meanwhile in Russia | unresolved |
| lost_tires08.webp | none | https://www.youtube.com/watch?v=2ysuwejHZEg | Meanwhile in Russia | unresolved |
| lost_tires09.webp | none | https://www.youtube.com/watch?v=2ysuwejHZEg | Meanwhile in Russia | unresolved |
| obstacles01_boulder.webp | none | http://cdpenterprises.com/lifestyle/productivity/turn-your-setbacks-into-success/ | CDPEnterprises | unresolved |
| obstacles02_rock.webp | none | https://www.beltandroad.news/2019/01/17/chinas-belt-road-initiative-faces-obstacles-in-2019/ | Belt & Road News | unresolved |
| obstacles03_cardboard_czech_hedgehog.webp | none | https://jasondeansart.com/sculpture/moveable-barriers/ | Jason Deans | unresolved |
| obstacles04_cardboard_czech_hedgehog.webp | none | https://jasondeansart.com/sculpture/moveable-barriers/ | Jason Deans | unresolved |
| obstacles05_cardboard_czech_hedgehog.webp | none | https://jasondeansart.com/sculpture/moveable-barriers/ | Jason Deans | unresolved |
| obstacles06_cardboard_czech_hedgehog.webp | none | https://jasondeansart.com/sculpture/moveable-barriers/ | Jason Deans | unresolved |
| obstacles07_czech_hedgehog.webp | none | https://www.etsy.com/listing/116401378/mini-czech-hedgehog-wwii-anti-tank | WalkersChopShop | unresolved |
| obstacles08_boulder2.webp | none | https://www.noordinaryhomestead.com/recover-unexpected-impediments-obstacles-failures | No Ordinary Homestead | unresolved |
| obstacles09_boulder3.webp | none | http://www.midforkrocks.com/post/201402-rock-on-road/ | Mid Fork Rocks | unresolved |
| obstacles10_boulder4.webp | none | https://www.stevecurtin.com/blog/obstacles/ | Steve Curtin | unresolved |
| obstacles11_boulder5.webp | none | https://www.flickr.com/photos/wsdot/albums/72157623228509590/ | Washington State Dept of Transportation | unresolved |
| obstacles12_rocks2.webp | none | null | malnit56 / tripadvisor.com | unresolved |
| obstacles12_rocks4.webp | none | null | malnit56 / tripadvisor.com | unresolved |
| obstacles12_rocks5.webp | none | null | malnit56 / tripadvisor.com | unresolved |
| obstacles12_rocks6.webp | none | null | malnit56 / tripadvisor.com | unresolved |
| vehicle01_man_carrying_dry_grass_on_bicycle.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:A_man_carrying_dry_grass_on_bicycle_for_domestic_animal_like_cows.jpg | KelvinJM, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |
| vehicle02_Broadmoor_Cones_Skidloader.webp | CC BY 2.5 | https://commons.wikimedia.org/wiki/File:Broadmoor9JanConesSkidloader.jpg | Infrogmation, CC BY 2.5 https://creativecommons.org/licenses/by/2.5/deed.en | computed_local |
| vehicle03_Fuhrwerke_in_China.webp | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Fuhrwerke_in_China.jpg | Manfred Kopka, CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ | computed_local |

| Licensing claim | Value | Evidence |
|---|---|---|
| Annotation licence | CC BY-SA 4.0 | documented_local |
| Annotation sources | data/credits.txt, docs/dataset.md, README.md | documented_local |
| Annotation terms URL | https://creativecommons.org/licenses/by-sa/4.0/ | documented_local |
| Code licence | MIT | documented_local |
| Code licence source | LICENSE | documented_local |
| Code licence scope | source code; data and annotations excluded | documented_local |
| Legal conclusion | not_made | documented_local |

The annotation and code licence statements are local documented claims, not legal advice or independently verified terms (`documented_local`). Local attribution is not proof of redistribution rights (`upstream_unverified`).

| Provenance property | Value | Evidence |
|---|---|---|
| Citation | Lis et al., Detecting the Unexpected via Image Resynthesis, ICCV 2019 | documented_local |
| Release identifier | null | upstream_unverified |
| Upstream status | upstream_unverified | upstream_unverified |
| Scene identity | unresolved | unresolved |
| Filename prefix is scene ID | false | computed_local |
| Local attribution is redistribution proof | false | upstream_unverified |
| Normal-road source selected | false | computed_local |

## 9. Documented claims, limitations and unresolved items

| Documented claim (`documented_local`) | Computed value (`computed_local`) | Definition | Treatment |
|---|---|---|---|
| Anomaly coverage is 9.8 percent of all pixels. (docs/dataset.md) | pooled 9.849561 percent; 0.374674-42.328559 percent per frame; median 6.622938 percent | pooled anomaly pixels / total pixels, six-decimal percent | report_both |
| Median instance is approximately 87 x 87 px; 35 of 201 are smaller than 32 x 32 px. (docs/dataset.md) | ROI area < 1024: 35/201; both dimensions < 32: 20/201; either dimension < 32: 46/201; median ROI equivalent square 86.7 px; median ROI bbox 85.0 x 107.0 px; median mask equivalent square 51.2 px | ROI area < 1024; both/either dimension < 32; sqrt(ROI area); median ROI bbox; sqrt(mask pixel count) | report_both |
| Filename prefixes are the natural scene grouping. (docs/dataset.md) | No scene IDs or source scene metadata exist locally; prefix counts are object categories only (animals 31, obstacles 15, cones 8, lost_tires 3, vehicle 3). | filename prefix before the first digit | report_gap |
| Per-image terms are recorded in credits.txt. (data/credits.txt) | 24/60 frames lack an explicit licence token; 4/60 lack a source URL; missing tokens remain unresolved. | explicit CC0, CC BY/CC BY-SA or public-domain token per credit block | mark_unresolved |
| Scene-grouped benchmark folds can support the separately reported threshold-tuned regime. (docs/dataset.md) | No benchmark scene identities exist locally; no folds, scene assignments or split hash are created. | benchmark scene identity and fold assignment | report_gap |
| The instance-mask pixel value equals the instance id. (docs/dataset.md) | 35/46 frames agree under the k-th-entry order mapping; 11/46 disagree; 48 value/entry mismatches are listed. | mask value k equals instances[k-1].id | report_both |

| Limitation | Statement | Evidence | Source |
|---|---|---|---|
| historical-fingerprint-local-reconstruction | The historical fingerprint recipe is a local reconstruction; matching it does not prove the original Stage 2 implementation byte layout. | upstream_unverified | specs/003-dataset-understanding/spec.md |
| visual-registration-unverified | Visual registration of frames, semantic masks and instance annotations was not assessed in the MVP. | unresolved | null |
| duplicates-method-limited | Exact, decoded-pixel and dHash checks are method-limited; no reported pair is not proof that no near-duplicate exists. | computed_local | data/frames/*.webp |
| source-groups-attribution-derived | Source groups are attribution-derived groups, not scene identities, split units or source rankings. | computed_local | data/credits.txt |
| upstream-provenance-unverified | No local release, version or checksum identifier verifies upstream provenance. | upstream_unverified | data/readme.md |
| per-image-licence-tokens-unresolved | Missing per-image licence tokens remain unresolved and are not evidence that an image is unlicensed. | unresolved | data/credits.txt |
| environment-commit-provenance | environment.commit is recorded provenance, not a revalidated git ancestry claim. | computed_local | specs/003-dataset-understanding/contracts/audit-cli.md |

| Unresolved item | Statement | Evidence | Source | Status |
|---|---|---|---|---|
| adr-0010-threshold-contradiction | ADR-0010 leaves the threshold contradiction unresolved. | unresolved | docs/adr/0010-model-lineup-and-evaluation-contract.md | open |

| Open item | Status | Evidence |
|---|---|---|
| P0-1 | open | unresolved |
| P0-2 | open | unresolved |
| P0-3 | open | unresolved |
| P0-4 | open | unresolved |
| G10 | open | unresolved |

P0-1 through P0-4, G10 and the ADR-0010 threshold contradiction remain open (`unresolved`). The audit makes no model, metric, threshold, class-map, split or promotion decision (`documented_local`).

## 10. Validation and output integrity

| Validation item | Value | Evidence |
|---|---|---|
| Schema | Draft 2020-12 validation passed before rendering | computed_local |
| Canonical command | make data-audit | computed_local |
| Source JSON SHA-256 | `46e50e8ce998139f5ce1b096df79dfd820fe0034e3faea1a7f73a756f14acec2` | computed_local |
| Output set | `roadanomaly-eda.json`, `roadanomaly-eda.md` | computed_local |
| Check mode | make data-audit-check | documented_local |

The JSON is authoritative; this report is derived from validated JSON bytes and adds only the source digest above (`computed_local`). The two output files are replaced individually, so a crash or second-replacement failure can leave a mixed pair that check mode detects (`computed_local`).

No class map, split, split hash, manifest, experiment record, figure, overlay, review ledger or normal-road readiness report was created (`computed_local`).

**Claim classification** (`computed_local`)

| Claim ID | Text | Evidence | Value | Definition | Source |
|---|---|---|---|---|---|
| fingerprint.match | The computed local fingerprint matches the historical baseline. | computed_local | {"computed": "7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2", "historical": "7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2", "status": "match"} | regular files under data/ (no symlinks), sorted by POSIX relative path; for each: UTF-8 path + NUL + raw 32-byte SHA-256 of content; no trailing NUL/newline; lowercase hex | data/ |
| inventory.counts | 60 frames, 60 label directories, 46 instance-annotated and 14 semantic-only frames. | computed_local | {"frame_count": 60, "frame_list_count": 60, "instance_frame_count": 46, "label_dir_count": 60, "semantic_only_frame_count": 14} | frame_list.json order and <frame>.labels directory membership | data/frame_list.json |
| inventory.annotation_integrity | Frame decoding, semantic values, colour mapping, contiguous instance IDs and cls=2 were checked. | computed_local | {"colour_mapping": {"anomaly": [255, 69, 0], "normal": [0, 0, 0]}, "colour_mapping_valid": true, "frame_decodable": true, "instance_class_id": 2, "instance_ids_contiguous": true, "label_files_complete": true, "semantic_values": [0, 2]} | All annotation_integrity flags are true only after their checks pass. | data/frames/*.labels |
| instance_semantic.exact | All 46 instance frames satisfy the instance/semantic invariant; 14 semantic-only frames are excluded. | computed_local | {"extra_instance_pixels": 0, "frames_checked": 46, "frames_exact_match": 46, "frames_mismatched": 0, "missing_instance_pixels": 0, "semantic_only_frames_excluded": 14} | union(instance values 1..N) == semantic value 2, per instance frame | data/frames/*.labels |
| coverage.pooled | Pooled anomaly coverage is 9.849561 percent. | computed_local | {"fraction": 0.09849561, "percent": 9.849561, "total_anomaly_pixels": 5446413, "total_pixels": 55296000} | total anomaly pixels / total pixels over all 60 frames | data/frames/*.labels/labels_semantic.png |
| coverage.range | Per-frame anomaly coverage ranges from 0.374674 to 42.328559 percent. | computed_local | {"maximum_percent": 42.328559, "median_percent": 6.622938, "minimum_percent": 0.374674} | anomaly pixels / (1280 x 720) | data/frames/*.labels/labels_semantic.png |
| coverage.below_one_percent | Six frames have per-frame anomaly coverage below one percent. | computed_local | ["animals02_Zagori_On_the_road_to_Papigko.webp", "animals11_Cock_Pheasant_on_Romford_Road.webp", "lost_tires03.webp", "lost_tires08.webp", "lost_tires09.webp", "obstacles12_rocks2.webp"] | per-frame percent < 1.0 | data/frames/*.labels/labels_semantic.png |
| categories.counts | Filename prefixes count five object categories; they are not scene IDs. | computed_local | {"classification": "object_category_not_scene", "counts": {"animals": 31, "cones": 8, "lost_tires": 3, "obstacles": 15, "vehicle": 3}, "total_frames": 60} | prefix before the first digit in the frame stem | data/frame_list.json |
| object_scale.counts | Object-scale counts expose all three small-object definitions. | computed_local | {"both_dimensions_below_32": 20, "denominator": 201, "either_dimension_below_32": 46, "roi_area_below_1024": 35} | (x1 - x0) x (y1 - y0), half-open extents | data/frames/*.labels/index.json |
| object_scale.medians | ROI and mask-pixel equivalent-square medians accompany the documented 87 x 87 claim. | computed_local | {"median_mask_equivalent_square_px": 51.2, "median_roi_equivalent_square_px": 86.7, "median_roi_height_px": 107.0, "median_roi_width_px": 85.0} | sqrt(ROI area) | data/frames/*.labels |
| instance_mapping.agreement | The k-th index-entry order mapping agrees in 35 frames and disagrees in 11. | computed_local | {"disagreeing_frames": ["animals05_cows_near_Phonsavan_Laos.webp", "animals08_on_the_main_street_of_village_Lin_Albania.webp", "animals10_bovine_cattle_beside_road.webp", "animals13_jeune_bovin_sur_la_route.webp", "animals17_E6_near_Kvaenangen.webp", "animals24_Sheep_Herders_Block_the_Road_Kaleybar_to_Eskanlu.webp", "animals29_Zebra_Crossing_Abbey_Road_Style.webp", "cones01_Beeston_MMB_A6_Middle_Street.webp", "lost_tires09.webp", "obstacles12_rocks6.webp", "vehicle03_Fuhrwerke_in_China.webp"], "frames_agreeing": 35, "frames_checked": 46, "frames_disagreeing": 11, "weaker_existing_test": {"name": "max(mask) == len(instances)", "passes": true}} | mask value k equals instances[k-1].id | data/frames/*.labels/index.json |
| roi.bounds | ROI findings are reported without clipping: 11 out of bounds, 17 non-tight, 201 centroids inside. | computed_local | {"centroids_inside": 201, "instances_checked": 201, "non_tight": 17, "out_of_bounds": 11} | x0 < 0 or y0 < 0 or x1 > 1280 or y1 > 720, half-open extents | data/frames/*.labels/index.json |
| duplicates.methods | Exact, decoded-pixel and dHash duplicate checks found no baseline pairs; the methods are limited. | computed_local | {"decoded_pairs": [], "dhash_method": "9x8 grayscale dHash, 64 bits; Hamming distance <= 6", "dhash_pairs": [], "exact_pairs": []} | 9x8 grayscale dHash, 64 bits; Hamming distance <= 6 | data/frames/*.webp |
| credits.coverage | All 60 frames have credit entries; 24 lack an explicit per-image licence token. | computed_local | {"coverage": 60, "missing_entries": [], "missing_licence_tokens": ["animals25_jablonna_dziki.webp", "animals28.webp", "animals30.webp", "animals31_deer.webp", "cones07.webp", "cones08_can.webp", "lost_tires03.webp", "lost_tires08.webp", "lost_tires09.webp", "obstacles01_boulder.webp", "obstacles02_rock.webp", "obstacles03_cardboard_czech_hedgehog.webp", "obstacles04_cardboard_czech_hedgehog.webp", "obstacles05_cardboard_czech_hedgehog.webp", "obstacles06_cardboard_czech_hedgehog.webp", "obstacles07_czech_hedgehog.webp", "obstacles08_boulder2.webp", "obstacles09_boulder3.webp", "obstacles10_boulder4.webp", "obstacles11_boulder5.webp", "obstacles12_rocks2.webp", "obstacles12_rocks4.webp", "obstacles12_rocks5.webp", "obstacles12_rocks6.webp"], "missing_source_urls": ["obstacles12_rocks2.webp", "obstacles12_rocks4.webp", "obstacles12_rocks5.webp", "obstacles12_rocks6.webp"]} | one credit block per frame stem in data/credits.txt | data/credits.txt |
| credits.source_groups | Four attribution-derived source groups cover 13 frames, including one group without a URL. | computed_local | {"frame_count": 13, "group_count": 4, "groups": [{"frame_count": 2, "frames": ["cones07.webp", "cones08_can.webp"], "group_id": "source-group-001", "source_url": "https://www.stuff.co.nz/auckland/local-news/papakura-courier/102189952/upsurge-in-traffic-turns-road-into-difficulttonegotiate-obstacle-course"}, {"frame_count": 3, "frames": ["lost_tires03.webp", "lost_tires08.webp", "lost_tires09.webp"], "group_id": "source-group-002", "source_url": "https://www.youtube.com/watch?v=2ysuwejHZEg"}, {"frame_count": 4, "frames": ["obstacles03_cardboard_czech_hedgehog.webp", "obstacles04_cardboard_czech_hedgehog.webp", "obstacles05_cardboard_czech_hedgehog.webp", "obstacles06_cardboard_czech_hedgehog.webp"], "group_id": "source-group-003", "source_url": "https://jasondeansart.com/sculpture/moveable-barriers/"}, {"frame_count": 4, "frames": ["obstacles12_rocks2.webp", "obstacles12_rocks4.webp", "obstacles12_rocks5.webp", "obstacles12_rocks6.webp"], "group_id": "source-group-004", "source_url": null}]} | frames sharing the same non-licence source URL, or the same URL-less credit block | data/credits.txt |
| credits.annotation_licence | The annotations are documented locally as CC BY-SA 4.0; no legal conclusion is made. | documented_local | {"claim": "CC BY-SA 4.0", "legal_conclusion": "not_made", "sources": ["data/credits.txt", "docs/dataset.md", "README.md"], "terms_url": "https://creativecommons.org/licenses/by-sa/4.0/"} | local documented claim; not independently verified | data/credits.txt |
| credits.code_licence | The source code is documented locally as MIT; data and annotations are excluded. | documented_local | {"claim": "MIT", "legal_conclusion": "not_made", "scope": "source code; data and annotations excluded", "source": "LICENSE"} | local documented claim; not independently verified | LICENSE |
| provenance.upstream | Upstream release provenance is unverified and scene identity is unresolved. | upstream_unverified | {"citation": "Lis et al., Detecting the Unexpected via Image Resynthesis, ICCV 2019", "filename_prefix_is_scene_id": false, "local_attribution_is_redistribution_proof": false, "release_identifier": null, "scene_identity": "unresolved", "upstream_status": "upstream_unverified"} | no local release, version or checksum identifier | data/readme.md |
| provenance.p0_g10 | P0-1 through P0-4 and G10 remain open. | unresolved | {"g10_status": "open", "p0_status": {"P0-1": "open", "P0-2": "open", "P0-3": "open", "P0-4": "open"}} | open scientific and source-readiness items | docs/validation/requirements-matrix.md |
| provenance.adr0010 | The ADR-0010 threshold contradiction remains open and is not reworded into a decision. | unresolved | [{"evidence_class": "unresolved", "item_id": "adr-0010-threshold-contradiction", "source": "docs/adr/0010-model-lineup-and-evaluation-contract.md", "statement": "ADR-0010 leaves the threshold contradiction unresolved.", "status": "open"}] | unresolved item; status open | docs/adr/0010-model-lineup-and-evaluation-contract.md |
| limitations.report | The report records method and evidence limits rather than converting them into certainty. | computed_local | ["historical-fingerprint-local-reconstruction", "visual-registration-unverified", "duplicates-method-limited", "source-groups-attribution-derived", "upstream-provenance-unverified", "per-image-licence-tokens-unresolved", "environment-commit-provenance"] | limitations list | dl/data/audit.py |
| documented_claims.comparisons | Six documented claims are compared with computed values without rewriting the source documents. | computed_local | ["coverage-rounding", "object-scale-87x87", "scene-prefix-grouping", "per-image-licence-completeness", "benchmark-scene-folds", "instance-id-equality"] | side-by-side documented and computed value | docs/dataset.md |
| documented.coverage-rounding | Anomaly coverage is 9.8 percent of all pixels. | documented_local | pooled 9.849561 percent; 0.374674-42.328559 percent per frame; median 6.622938 percent | pooled anomaly pixels / total pixels, six-decimal percent | docs/dataset.md |
| documented.object-scale-87x87 | Median instance is approximately 87 x 87 px; 35 of 201 are smaller than 32 x 32 px. | documented_local | ROI area < 1024: 35/201; both dimensions < 32: 20/201; either dimension < 32: 46/201; median ROI equivalent square 86.7 px; median ROI bbox 85.0 x 107.0 px; median mask equivalent square 51.2 px | ROI area < 1024; both/either dimension < 32; sqrt(ROI area); median ROI bbox; sqrt(mask pixel count) | docs/dataset.md |
| documented.scene-prefix-grouping | Filename prefixes are the natural scene grouping. | documented_local | No scene IDs or source scene metadata exist locally; prefix counts are object categories only (animals 31, obstacles 15, cones 8, lost_tires 3, vehicle 3). | filename prefix before the first digit | docs/dataset.md |
| documented.per-image-licence-completeness | Per-image terms are recorded in credits.txt. | unresolved | 24/60 frames lack an explicit licence token; 4/60 lack a source URL; missing tokens remain unresolved. | explicit CC0, CC BY/CC BY-SA or public-domain token per credit block | data/credits.txt |
| documented.benchmark-scene-folds | Scene-grouped benchmark folds can support the separately reported threshold-tuned regime. | documented_local | No benchmark scene identities exist locally; no folds, scene assignments or split hash are created. | benchmark scene identity and fold assignment | docs/dataset.md |
| documented.instance-id-equality | The instance-mask pixel value equals the instance id. | documented_local | 35/46 frames agree under the k-th-entry order mapping; 11/46 disagree; 48 value/entry mismatches are listed. | mask value k equals instances[k-1].id | docs/dataset.md |
