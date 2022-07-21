# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

import dash
from dash.dependencies import Input, Output, State


def add_callbacks(dash_app, viz_server):
    dash_app.callback([Output("gofast-button", "children")],
                      [Input("nb_step_go_fast", "value")]
                     )(viz_server.change_nb_step_go_fast)

    # handle the press to one of the button to change the units
    dash_app.callback([Output("unit_trigger_rt_graph", "n_clicks"),
                       Output("unit_trigger_for_graph", "n_clicks"),
                      ],
                      [Input("line-info-dropdown", "value"),
                       Input("line-side-dropdown", "value"),
                       Input("load-info-dropdown", "value"),
                       Input("gen-info-dropdown", "value"),
                       Input("stor-info-dropdown", "value")
                      ],
                      [State("unit_trigger_rt_graph", "n_clicks"),
                       State("unit_trigger_for_graph", "n_clicks")
                      ]
                     )(viz_server.unit_clicked)

    # handle the interaction with the graph
    dash_app.callback([Output("do_display_action", "value"),
                       Output("generator_clicked", "style"),
                       Output("gen-redisp-curtail", "children"),
                       Output("gen-id-hidden", "children"),
                       Output("gen-id-clicked", "children"),
                       Output("gen-dispatch", "min"),
                       Output("gen-dispatch", "max"),
                       Output("gen-dispatch", "value"),
                       Output("gen_p", "children"),
                       Output("target_disp", "children"),
                       Output("actual_disp", "children"),

                       Output("storage_clicked", "style"),
                       Output("storage-id-hidden", "children"),
                       Output("stor-id-clicked", "children"),
                       Output("storage-power-input", "min"),
                       Output("storage-power-input", "max"),
                       Output("storage-power-input", "value"),
                       Output("storage_p", "children"),
                       Output("storage_energy", "children"),

                       Output("line_clicked", "style"),
                       Output("line-id-hidden", "children"),
                       Output("line-id-clicked", "children"),
                       Output("line-status-input", "value"),
                       Output("line_flow", "children"),

                       Output("sub_clicked", "style"),
                       Output("sub-id-hidden", "children"),
                       Output("sub-id-clicked", "children"),
                    #    Output("graph_clicked_sub", "figure"),
                       Output("update_substation_layout_clicked_from_grid", "n_clicks"),
                      ],
                      [Input('real-time-graph', 'clickData'),
                       Input("back-button", "n_clicks"),
                       Input("step-button", "n_clicks"),
                       Input("simulate-button", "n_clicks"),
                       Input("go-button", "n_clicks"),
                       Input("gofast-button", "n_clicks"),
                       Input("go_till_game_over-button", "n_clicks"),
                       Input("go_till_game_over_auto-button", "n_clicks"),
                      ])(viz_server.display_click_data)

    # handle display of the action, if needed
    dash_app.callback([Output("current_action", "children"),
                       Output("which_action_button", "value"),
                       Output("update_substation_layout_clicked_from_sub", "n_clicks"),
                       Output("action_buttons", "style"),
                      ],
                      [Input("which_action_button", "value"),
                       Input("do_display_action", "value"),
                       Input("gen-redisp-curtail", "children"),
                       Input("gen-id-hidden", "children"),
                       Input('gen-dispatch', "value"),
                       Input("storage-id-hidden", "children"),
                       Input('storage-power-input', "value"),
                       Input("line-id-hidden", "children"),
                       Input('line-status-input', "value"),
                       Input('sub-id-hidden', "children"),
                       Input("graph_clicked_sub", "clickData"),
                       Input('real-time-graph', 'clickData'),
                      ],
                      [State("recommendations_container", "is_open")]
    )(viz_server.display_action_fun)

    # plot the substation that changes when we click
    dash_app.callback([Output("graph_clicked_sub", "figure")],
                      [Input("update_substation_layout_clicked_from_sub", "n_clicks"),
                       Input("update_substation_layout_clicked_from_grid", "n_clicks"),
                      ])(viz_server.display_grid_substation)

    # handle the interaction with self.env, that should be done all in one function, otherwise
    # there are concurrency issues
    dash_app.callback([
                       # trigger the computation if needed
                       Output("trigger_computation", "value"),
                       # update the button color / shape / etc. if needed
                       Output("step-button", "className"),
                       Output("simulate-button", "className"),
                       Output("back-button", "className"),
                       Output("reset-button", "className"),
                       Output("go-button", "className"),
                       Output("gofast-button", "className"),
                       Output("go_till_game_over-button", "className"),
                       Output("go_till_game_over_auto-button", "className"),
                       Output("is_computing_left", "style"),
                       Output("is_computing_right", "style"),
                       Output("change_graph_title", "n_clicks"),
                       Output("update_progress_bar_from_act", "n_clicks"),
                       Output("check_issue", "n_clicks"),
                      ],
                      [Input("step-button", "n_clicks"),
                       Input("simulate-button", "n_clicks"),
                       Input("back-button", "n_clicks"),
                       Input("reset-button", "n_clicks"),
                       Input("go-button", "n_clicks"),
                       Input("gofast-button", "n_clicks"),
                       Input("go_till_game_over-button", "n_clicks"),
                       Input("go_till_game_over_auto-button", "n_clicks"),
                       Input("untilgo_butt_call_act_on_env", "value"),
                       Input("selfloop_call_act_on_env", "value"),
                       Input("timer", "n_intervals"),
                      ],
                      [State("act_on_env_trigger_rt", "n_clicks"),
                       State("act_on_env_trigger_for", "n_clicks"),
                       State("act_on_env_call_selfloop", "value"),
                       State("recommendations_container", "is_open"),
                       State("selected_recommendation_store", "data"),
                      ]
                     )(viz_server.handle_act_on_env)

    dash_app.callback([Output("act_on_env_trigger_rt", "n_clicks"),
                       Output("act_on_env_trigger_for", "n_clicks")
                      ],
                      [Input("trigger_computation", "value"),
                       Input("recompute_rt_from_timeline", "n_clicks"),
                       Input("variant_tree_added", "n_clicks"),
                      ]
                      )(viz_server.computation_wrapper)

    # handle triggers: refresh of the figures for real time (graph part)
    dash_app.callback([Output("figrt_trigger_temporal_figs", "n_clicks"),
                       Output("figrt_trigger_rt_graph", "n_clicks"),
                       Output("figrt_trigger_for_graph", "n_clicks"),
                       Output("timeline_graph", "figure"),
                       Output("update_progress_bar_from_figs", "n_clicks")
                      ],
                      [Input("act_on_env_trigger_rt", "n_clicks")],
                      []
                     )(viz_server.update_rt_fig)

    dash_app.callback([
                       Output("scenario_progression", "value"),
                       Output("scenario_progression", "label"),
                       Output("scenario_progression", "color"),
                      ],[
                       Input("update_progress_bar_from_act", "n_clicks"),
                       Input("update_progress_bar_from_figs", "n_clicks"),
                      ])(viz_server.update_progress_bar)
    # handle triggers: refresh of the figures for the forecast
    dash_app.callback([Output("figfor_trigger_for_graph", "n_clicks")],
                      [Input("act_on_env_trigger_for", "n_clicks")],
                      []
                     )(viz_server.update_simulated_fig)

    # final graph display
    # handle triggers: refresh the figures (temporal series part)
    dash_app.callback([Output("graph_gen_load", "figure"),
                       Output("graph_flow_cap", "figure"),
                      ],
                      [Input("figrt_trigger_temporal_figs", "n_clicks"),
                       Input("showtempo_trigger_rt_graph", "n_clicks")
                      ],
                     )(viz_server.update_temporal_figs)

    # dash_app.callback([Output('temporal_graphs', "style"),
    #                    Output("showtempo_trigger_rt_graph", "n_clicks")
    #                    ],
    #                   [Input('show-temporal-graph', "value")]
    #                   )(self.show_hide_tempo_graph)

    # handle final graph of the real time grid
    dash_app.callback([Output("real-time-graph", "figure"),
                       Output("rt_date_time", "children"),
                       Output("trigger_rt_extra_info", "n_clicks")
                      ],
                      [Input("figrt_trigger_rt_graph", "n_clicks"),
                       Input("unit_trigger_rt_graph", "n_clicks"),
                      ]
                     )(viz_server.update_rt_graph_figs)

    # handle final graph for the forecast grid
    dash_app.callback([Output("simulated-graph", "figure"),
                       Output("forecast_date_time", "children"),
                       Output("trigger_for_extra_info", "n_clicks")
                      ],
                      [Input("figrt_trigger_for_graph", "n_clicks"),
                       Input("figfor_trigger_for_graph", "n_clicks"),
                       Input("unit_trigger_for_graph", "n_clicks"),
                      ]
                     )(viz_server.update_for_graph_figs)

    if viz_server._app_heroku is False:
        # this is deactivated on heroku at the moment !
        # load the assistant
        dash_app.callback(
            [
                Output("current_assistant_path", "children"),
                Output("clear_assistant_path", "n_clicks"),
                Output("loading_assistant_output", "children"),
            ],
            [Input("load_assistant_button", "n_clicks")],
            [State("select_assistant", "value")],
            prevent_initial_call=True,
        )(viz_server.load_assistant)

        dash_app.callback(
            [Output("select_assistant", "value")],
            [Input("clear_assistant_path", "n_clicks")],
            prevent_initial_call=True,
        )(viz_server.clear_loading)

        # save the current experiment
        dash_app.callback([Output("current_save_path", "children"),
                           Output("loading_save_output", "children"),
                          ],
                          [Input("save_expe_button", "n_clicks")],
                          [State("save_expe", "value")]
                         )(viz_server.save_expe)

    # tell if action was illegal
    dash_app.callback([Output("forecast_extra_info", "style")],
                      [Input("trigger_for_extra_info", "n_clicks")]
                     )(viz_server.tell_illegal_for)
    dash_app.callback([Output("rt_extra_info", "style")],
                      [Input("trigger_rt_extra_info", "n_clicks")]
                     )(viz_server.tell_illegal_rt)

    # callback for the timeline
    dash_app.callback([Output("recompute_rt_from_timeline", "n_clicks")],
                      [Input('timeline_graph', 'clickData')])(viz_server.timeline_set_time)

    # callbacks when the "reset" button is pressed
    dash_app.callback([Output("scenario_id_title", "children"),
                       Output("scenario_seed_title", "children"),
                       Output("chronic_names", "value"),
                       Output("set_seed", "value"),
                      ],
                      [Input("change_graph_title", "n_clicks")])(viz_server.change_graph_title)

    # set the chronics
    dash_app.callback([Output("chronic_names_dummy_output", "n_clicks")],
                      [Input("chronic_names", "value")])(viz_server.set_chronics)

    # set the seed
    dash_app.callback([Output("set_seed_dummy_output", "n_clicks")],
                      [Input("set_seed", "value")])(viz_server.set_seed)

    # trigger the modal issue
    dash_app.callback(
        [
            Output("modal_issue", "is_open"),
            Output("modal_issue_text", "children"),
        ],
        [
            Input("check_issue", "n_clicks"),
            # Close modal when clicking on Show more
            Input("show_more_issue", "n_clicks"),
        ],
        [
            State("modal_issue", "is_open"),
        ],
        prevent_initial_call=True,
    )(viz_server.check_issue)

    # show the recommendations table
    dash_app.callback(
        [
            Output("recommendations_div", "children"),
            Output("recommendations_container", "is_open"),
            Output("recommendations_store", "data"),
            Output("recommendations_message", "children"),
            Output("recommendations_added_to_variant_trees_store", "data"),
            Output("variant_tree_added", "n_clicks"),
        ],
        [
            Input("show_more_issue", "n_clicks"),
            Input("close_recommendations_button", "n_clicks"),
            Input("add_to_variant_trees_button", "n_clicks"),
            Input("apply_recommendation_button", "n_clicks"),
            Input("integrate_manual_action", "n_clicks"),
            Input("add_to_knowledge_base_button", "n_clicks"),
            Input("add_expert_recommendation", "n_clicks"),
        ],
        [
            State("recommendations_container", "is_open"),
            State("recommendations_store", "data"),
            State("selected_recommendation_store", "data"),
            State("recommendations_added_to_variant_trees_store", "data"),
        ],
        # prevent_initial_call=True,
    )(viz_server.handle_recommendations)

    dash_app.callback(
        [
            Output("loading_recommendations_output", "children"),
        ],
        [
            Input("show_more_issue", "n_clicks"),
            Input("integrate_manual_action", "n_clicks"),
        ],
        # prevent_initial_call=True,
    )(viz_server.loading_recommendations_table)

    dash_app.callback(
        [
            Output("selected_recommendation_store", "data"),
        ],
        [
            Input("recommendations_table", "selected_rows"),
        ],
        [
            State("recommendations_store", "data"),
        ],
        prevent_initial_call=True,
    )(viz_server.select_recommendation)

    # dropdown mode
    dash_app.callback(
        [
            Output("controls_manual_collapse", "is_open"),
            Output("controls_auto_collapse", "is_open"),
        ],
        [
            Input("mode_names", "value"),
        ],
        [
            State("controls_manual_collapse", "is_open"),
            State("controls_auto_collapse", "is_open"),
        ],
    )(viz_server.dropdown_mode)

    dash_app.callback(
        [
            dash.dependencies.Output('tabs-main-view', 'value'),
        ],
        [
            dash.dependencies.Input('expert_agent_button', 'n_clicks'),
            dash.dependencies.Input('add_expert_recommendation', 'n_clicks'),
        ],
        prevent_initial_call=True,
    )(viz_server.open_tab)
